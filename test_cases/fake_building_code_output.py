"""Create a fake building code output file for testing purposes.

In one building code pdf file, we have nested components. Here's the rough structure for each component:

class Component:
    id: (node_type, node_id)
    parent_id: (node_type, node_id) --> if root, ("root", 0)
    title: str
    text: str

The output should be in single-line json format, like so:
{(node_type, node_id): {"parent_id": (node_type, node_id), "text": str}}
...

node types: "root", "chapter", "article", "section", "subsection", "number", "letter", "subletter", "roman_numeral".

Example usage:
poetry run python fake_building_code_output.py -n 2 -l 5 -w 12 -s 0 -o fake_building_code_output.json
"""

import argparse
import sys
import json
import dataclasses
import random

import typing


@dataclasses.dataclass
class Component:
    id: typing.Tuple[str, int]
    parent_id: typing.Tuple[str, int]
    title: str  # can be empty string
    text: str  # can be empty string

    def __str__(self):
        return json.dumps(dataclasses.asdict(self))


# store node types in a indexable list
NODE_TYPES = ["root", "chapter", "article", "section", "subsection", "number", "letter", "subletter", "roman_numeral"]


def create_fake_building_code_output(
    num_components: int = 3,
    creating_from: str = "root",
    num_words: int = 100,
    seed: int = 0,
    ids_used_so_far: typing.Set[typing.Tuple[str, int]] = set(),
):
    """From a creating_from node, create num_components components of the next
    tier, with num_words characters in each component's text. Calls itself
    recursively to create the next tier of components. Make sure there are no
    overlapping node ids when collecting all the components together.

    Only roman_numeral nodes don't have to create children."""
    random.seed(seed)
    components = []

    # check if this is the last tier
    if creating_from == "roman_numeral":
        return components

    # create components
    for i in range(num_components):
        # create node id
        node_id = random.randint(0, 1000000)
        while (creating_from, node_id) in ids_used_so_far:
            node_id = random.randint(0, 1000000)
        ids_used_so_far.add((creating_from, node_id))

        # create component
        component = Component(
            id=(creating_from, node_id),
            parent_id=(creating_from, 0),
            # text="".join([random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(num_words)]),
            # make it into some fake words (foo bar baz)
            title=" ".join([random.choice(["foo", "bar", "baz"]) for _ in range(int(num_words / 3))]),
            text=" ".join([random.choice(["foo", "bar", "baz"]) for _ in range(num_words)]),
        )
        components.append(component)

        # create children
        components.extend(
            create_fake_building_code_output(
                num_components=num_components,
                creating_from=NODE_TYPES[NODE_TYPES.index(creating_from) + 1],
                num_words=num_words,
                seed=seed,
                ids_used_so_far=ids_used_so_far,
            )
        )

    return components


def write_to_file(components, output_file: str = "fake_building_code_output.json"):
    with open(output_file, "w") as f:
        for component in components:
            f.write(str(component) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create fake building code output file for testing purposes.')
    parser.add_argument(
        '-n', '--num_components', type=int, default=10,
        help='Number of components in the building code output file.'
    )
    parser.add_argument(
        '-l', '--num_levels', type=int, default=5,
        help='Number of levels in the building code output file.'
    )
    parser.add_argument(
        '-w', '--num_words', type=int, default=100,
        help='Number of characters in the building code output file.'
    )
    parser.add_argument(
        '-s', '--seed', type=int, default=0,
        help='Random seed.'
    )
    parser.add_argument(
        '-o', '--output_file', type=str, default="fake_building_code_output.json",
        help='Output file name.'
    )
    args = parser.parse_args()

    # create components
    components = create_fake_building_code_output(
        num_components=args.num_components,
        creating_from=NODE_TYPES[0],
        num_words=args.num_words,
        seed=args.seed,
        ids_used_so_far=set(),
    )

    # write to file
    write_to_file(components, output_file=args.output_file)