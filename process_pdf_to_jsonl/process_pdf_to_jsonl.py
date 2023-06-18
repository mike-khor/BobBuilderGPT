"""Create JSONL file from a specific PDF.

This is a parallellizable process, as in, if n_process is set to > 1, then
we will split the PDF into n_process chunks, and process each chunk in parallel
using the multiprocessing library.

Example usage:
poetry run python process_pdf_to_jsonl.py -n 4 -s 12 -e 4850
"""
import argparse
import typing
import re
import csv
import json
import multiprocessing

import pandas as pd
import PyPDF2


text_list = []
DEFAULT_STARTING_PAGE = 12
DEFAULT_END_PAGE = 2000
PDF_PATH = '../2022_ca_designer_collection_1st_ptg_rev.pdf'
DEFAULT_OUTPUT_FILE="building_code_output.jsonl"

def open_pdf_to_dataframe(
    starting_page: int = DEFAULT_STARTING_PAGE,
    ending_page: int = DEFAULT_END_PAGE,
):
    """Open PDF and return dataframe with text from each page.

    Can specify a max page number to read from."""
    with open(PDF_PATH, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        for page_number in range(starting_page, ending_page):
            print(page_number)
            text = reader.pages[page_number].extract_text()
            text_list.append([text])

    df = pd.DataFrame(text_list, columns=['Text'])
    # df.to_csv('ca_codes.csv', index=False)
    return df


def process_text(row):
    text = row['Text']
    page_number = None

    if row.name % 2 == 0:  # Even page
        match = re.search(r'(.*?)(\n?)(2022 CALIFORNIA ADMINISTRATIVE CODE )(\d+-\d+)(.*)(Copyright © 2022 ICC)', text, re.DOTALL)
        if match:
            page_number = match.group(4)
            text = match.group(5)
    else:  # Odd page
        match = re.search(r'(.*?)(\n?)(\d+-\d+)( 2022 CALIFORNIA ADMINISTRATIVE CODE)(.*)(Copyright © 2022 ICC)', text, re.DOTALL)
        if match:
            text = match.group(5)
            page_number = match.group(3)

    # any text with " should be modified to be json.loads compatible
    # text = text.replace('"', "'")

    # Return a new row
    return pd.Series([page_number, text])


LEVEL_PATTERNS = {
    "root": None,
    "chapter": r"(CHAPTER \d+)(.*?)(ARTICLE \d.*?)(?=CHAPTER \d+|$)",
    "article": r"(ARTICLE \d+)(.*?)(\d+-\d+\..*?)(?=ARTICLE \d+|$)",
    "section": r"(\d+-\d+\.)(.*?\.)(.*?)(?=\d+-\d+\.|$)",
    "subsection": r"\n(\([a-z]\)\s)(.*?)(.*?)(?=\n\([a-z]\)\s|$)",
    "number": r"\n(\d+\.\s)(.*?)(.*?)(?=\n\d+\.\s|$)",
    "letter": r"\n([A-Z]\s)(.*?\.)(.*?)(?=[A-Z]\w*|$)",
    "subletter": r"\n\((\d+\s)\)(.*?\.)(.*?)(?=\(\d+\)|$)",
    "roman_numeral": r"\n\(([ivxlcdm]+\s)\)(.*?\.)(.*?)(?=\([ivxlcdm]+\)|$)",
}

LEVEL_PREFIX = "level_"

def parse_text(
    text: str,
    last_parent_node_level_and_id: typing.Tuple[int, int] = (0, 0),  # to keep track of lineage
    current_level: int = 0,  # current level to scope in. all matches are matching current_level + 1, and a new node assigned
) -> typing.List[typing.Dict[str, typing.Any]]:
    """Parse text into nested dicts.

    last_parent_node_id: a tuple of (parent_level, parent_node_id)
    """
    result = []
    next_level = current_level + 1
    last_parent_node_level, last_parent_node_id = last_parent_node_level_and_id

    # Base case: if level is equal to or exceeds the length of LEVEL_PATTERNS,
    # this means we've reached the lowest level of the text. Proceed to return
    # text in a list.
    if current_level >= len(LEVEL_PATTERNS) - 1:
        # return [[text.replace('-\n', '').replace('\n', ' ').strip(), '']]
        # return [my_p_node,assign_node(),text.replace('-\n', '').replace('\n', ' ').strip(),""]
        text_clean = text.replace('-\n', '').replace('\n', ' ').strip()
        if text_clean == "":
            return []
        return [
            {
                "id": [f"{LEVEL_PREFIX}{current_level}", assign_node()],
                "parent_id": [f"{LEVEL_PREFIX}{last_parent_node_level}", last_parent_node_id],
                "text": text_clean,
                "title": "",
            }
        ]

    # all other cases: find all matches for the next level
    match_list: typing.List[str] = re.findall(list(LEVEL_PATTERNS.values())[next_level], text, re.DOTALL)

    # If there's no match, it's fine, try going to the next, even lower level
    # keep the same parent ID however
    if len(match_list) == 0:
        return parse_text(text, last_parent_node_level_and_id, current_level=next_level)

    for match in match_list:
        # found some matches! let's assign a node ID for each first
        node_id = assign_node()
        pattern, title, following_text = match[0], match[1], match[2]

        # if level == 3:
        #     print(f"pattern: {pattern}, title: {title}, following_text: {following_text[:300]}")

        # result.append([my_p_node,node,pattern.replace('-\n', '').replace('\n', ' ').strip(), title.replace('-\n', '').replace('\n', ' ').strip()])

        pattern_clean = pattern.replace('-\n', '').replace('\n', ' ').strip()
        title_clean = title.replace('-\n', '').replace('\n', ' ').strip()

        result += [
            {
                "id": [f"{LEVEL_PREFIX}{next_level}", node_id],
                "parent_id": [f"{LEVEL_PREFIX}{last_parent_node_level}", last_parent_node_id],
                "text": title_clean,
                "title": pattern_clean,
            }
        ]

        # Apply the same parsing process for the rest of the text by increasing level
        if next_level < len(LEVEL_PATTERNS) - 1:
            remaining_parts = parse_text(following_text, (next_level, node_id), next_level)  # this matched node with a new assigned ID is now the latest parent
        # if it's the last level, we already have the supporting text, no need to parse further

        result += remaining_parts #'node:'+str(node),'p_node:'+str(p_node)

    return result


def write_to_file(components, output_file: str = DEFAULT_OUTPUT_FILE):
    # output should be structured like this:
    # {"id": ["root", 885440], "parent_id": ["root", 0], "title": "bar bar foo bar", "text": "baz bar bar bar bar bar baz foo baz foo bar foo"}
    # {"id": ["chapter", 885440], "parent_id": ["chapter", 0], "title": "bar bar foo bar", "text": "baz bar bar bar bar bar baz foo baz foo bar foo"}
    with open(output_file, "w") as f:
        for component in components:
            f.write(json.dumps(component) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create fake building code output file for testing purposes.')
    parser.add_argument(
        '-n', '--num_processes', type=int, default=1,
        help='Number of processes to use.'
    )
    parser.add_argument(
        '-s', '--starting_page', type=int, default=DEFAULT_STARTING_PAGE,
        help='Starting page number.'
    )
    parser.add_argument(
        '-e', '--ending_page', type=int, default=DEFAULT_END_PAGE,
        help='Ending page number.'
    )
    parser.add_argument(
        '-o', '--output_file', type=str, default=DEFAULT_OUTPUT_FILE,
        help='Output file name.'
    )

    args = parser.parse_args()

    # if num_processes is more than 1, then we will split the PDF into
    # num_processes chunks, and process each chunk in parallel using the
    # multiprocessing library.
    # if args.num_processes > 1:
    #     # Create a list of tuples, each tuple is a starting and ending page
    #     # number that we will process in parallel
    #     page_ranges = []
    #     num_pages = args.ending_page - args.starting_page
    #     pages_per_process = num_pages // args.num_processes
    #     for i in range(0, args.num_processes):
    #         start_page = args.starting_page + i * pages_per_process
    #         end_page = start_page + pages_per_process
    #         page_ranges.append((start_page, end_page))

    #     # Add the remainder to the last process
    #     page_ranges[-1] = (page_ranges[-1][0], args.ending_page)

    #     # Create a multiprocessing pool and process each of the page ranges
    #     pool = multiprocessing.Pool(args.num_processes)
    #     results = pool.starmap(open_pdf_to_dataframe, page_ranges)
    #     pool.close()
    #     pool.join()

    #     # Combine the results into a single DataFrame
    #     df = pd.concat(results, ignore_index=True)

    # else:
    df = open_pdf_to_dataframe(
        starting_page=args.starting_page,
        ending_page=args.ending_page,
    )

    # Apply the function to every row in the DataFrame
    df[['Page', 'Text']] = df.apply(process_text, axis=1)

    ca_codes = []
    for pagenum in range(len(df)):
        content = df.iloc[pagenum][0]
        ca_codes.append(content)
    ca_concatenated_string = ''.join(ca_codes)

    nodes = []
    def assign_node():
        global nodes
        if len(nodes) == 0:
            nodes.append(60000000)
            return 60000000
        else:
            node = max(nodes) + 1
            nodes.append(node)
            return node


    ca_parsed_text = parse_text(ca_concatenated_string)
    write_to_file(ca_parsed_text, output_file=args.output_file)
