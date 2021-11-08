"""A DataSet for Java files."""

import hashlib

import datasets

_CITATION = ""


_DESCRIPTION = ""

# TODO: Add a link to an official homepage for the dataset here
_HOMEPAGE = ""

# TODO: Add the licence for the dataset here if you can find it
_LICENSE = ""


class JavaDataset(datasets.GeneratorBasedBuilder):
    """This Dataset is designed to return Java code extracted from files."""

    VERSION = datasets.Version("1.1.0")

    BUILDER_CONFIGS = []

    def _info(self):
        features = datasets.Features(
            {
                "code": datasets.Value("string"),
            }
        )
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            supervised_keys=None,
            homepage=_HOMEPAGE,
            license=_LICENSE,
            citation=_CITATION,
        )

    def _split_generators(self, dl_manager):
        """Returns SplitGenerators."""
        my_files = self.config.data_files
        data_dir = dl_manager.download_and_extract(my_files)
        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN,
                gen_kwargs={
                    "filepath": data_dir['train'],
                    "split": "train",
                },
            ),
        ]

    def _generate_examples(self, filepath, split):
        """ Yields examples as (key, example) tuples. """

        with open(filepath, encoding="utf-8") as f:
            id_ = str(hashlib.sha1(filepath.encode('utf-8')))
            data = f.read()
            yield id_, { 
                    "code": data
                    }
