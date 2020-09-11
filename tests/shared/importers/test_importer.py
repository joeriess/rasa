import asyncio
import os
from pathlib import Path
from typing import Text, Dict, Type, List

import pytest

from rasa.constants import DEFAULT_CONFIG_PATH, DEFAULT_DOMAIN_PATH, DEFAULT_DATA_PATH
import rasa.shared.utils.io
import rasa.shared.core.constants
from rasa.shared.core.events import SlotSet, UserUttered, ActionExecuted
from rasa.shared.core.training_data.structures import StoryStep, StoryGraph
from rasa.shared.importers.importer import (
    CombinedDataImporter,
    TrainingDataImporter,
    NluDataImporter,
    CoreDataImporter,
    E2EImporter,
    RetrievalModelsDataImporter,
)
from rasa.shared.importers.multi_project import MultiProjectImporter
from rasa.shared.importers.rasa import RasaFileImporter
from rasa.shared.nlu.constants import ACTION_TEXT, ACTION_NAME, INTENT_NAME, TEXT
from rasa.shared.nlu.training_data.message import Message


async def test_use_of_interface():
    importer = TrainingDataImporter()

    functions_to_test = [
        lambda: importer.get_config(),
        lambda: importer.get_stories(),
        lambda: importer.get_nlu_data(),
        lambda: importer.get_domain(),
    ]
    for f in functions_to_test:
        with pytest.raises(NotImplementedError):
            await f()


async def test_combined_file_importer_with_single_importer(project: Text):
    config_path = os.path.join(project, DEFAULT_CONFIG_PATH)
    domain_path = os.path.join(project, DEFAULT_DOMAIN_PATH)
    default_data_path = os.path.join(project, DEFAULT_DATA_PATH)

    importer = RasaFileImporter(config_path, domain_path, [default_data_path])
    combined = CombinedDataImporter([importer])

    assert await importer.get_config() == await combined.get_config()
    actual_domain = await combined.get_domain()
    expected_domain = await importer.get_domain()
    assert hash(actual_domain) == hash(expected_domain)

    actual_training_data = await combined.get_nlu_data()
    expected_training_data = await importer.get_nlu_data()
    assert hash(actual_training_data) == hash(expected_training_data)

    expected_stories = await importer.get_stories()
    actual_stories = await combined.get_stories()

    assert actual_stories.as_story_string() == expected_stories.as_story_string()


@pytest.mark.parametrize(
    "config, expected",
    [
        ({}, [RasaFileImporter]),
        ({"importers": []}, [RasaFileImporter]),
        ({"importers": [{"name": "RasaFileImporter"}]}, [RasaFileImporter]),
        ({"importers": [{"name": "NotExistingModule"}]}, [RasaFileImporter]),
        (
            {
                "importers": [
                    {"name": "rasa.shared.importers.multi_project.MultiProjectImporter"}
                ]
            },
            [MultiProjectImporter],
        ),
        ({"importers": [{"name": "MultiProjectImporter"}]}, [MultiProjectImporter]),
        (
            {
                "importers": [
                    {"name": "RasaFileImporter"},
                    {"name": "MultiProjectImporter"},
                ]
            },
            [RasaFileImporter, MultiProjectImporter],
        ),
    ],
)
def test_load_from_dict(
    config: Dict, expected: List[Type["TrainingDataImporter"]], project: Text
):
    config_path = os.path.join(project, DEFAULT_CONFIG_PATH)
    domain_path = os.path.join(project, DEFAULT_DOMAIN_PATH)
    default_data_path = os.path.join(project, DEFAULT_DATA_PATH)
    actual = TrainingDataImporter.load_from_dict(
        config, config_path, domain_path, [default_data_path]
    )

    assert isinstance(actual, E2EImporter)
    assert isinstance(actual.importer, RetrievalModelsDataImporter)

    actual_importers = [i.__class__ for i in actual.importer._importer._importers]
    assert actual_importers == expected


def test_load_from_config(tmpdir: Path):
    config_path = str(tmpdir / "config.yml")

    rasa.shared.utils.io.write_yaml(
        {"importers": [{"name": "MultiProjectImporter"}]}, config_path
    )

    importer = TrainingDataImporter.load_from_config(config_path)
    assert isinstance(importer, E2EImporter)
    assert isinstance(importer.importer, RetrievalModelsDataImporter)
    assert isinstance(importer.importer._importer._importers[0], MultiProjectImporter)


async def test_nlu_only(project: Text):
    config_path = os.path.join(project, DEFAULT_CONFIG_PATH)
    default_data_path = os.path.join(project, DEFAULT_DATA_PATH)
    actual = TrainingDataImporter.load_nlu_importer_from_config(
        config_path, training_data_paths=[default_data_path]
    )

    assert isinstance(actual, NluDataImporter)
    assert isinstance(actual._importer, RetrievalModelsDataImporter)

    stories = await actual.get_stories()
    assert stories.is_empty()

    domain = await actual.get_domain()
    assert domain.is_empty()

    config = await actual.get_config()
    assert config

    nlu_data = await actual.get_nlu_data()
    assert not nlu_data.is_empty()


async def test_core_only(project: Text):
    config_path = os.path.join(project, DEFAULT_CONFIG_PATH)
    domain_path = os.path.join(project, DEFAULT_DOMAIN_PATH)
    default_data_path = os.path.join(project, DEFAULT_DATA_PATH)
    actual = TrainingDataImporter.load_core_importer_from_config(
        config_path, domain_path, training_data_paths=[default_data_path]
    )

    assert isinstance(actual, CoreDataImporter)

    stories = await actual.get_stories()
    assert not stories.is_empty()

    domain = await actual.get_domain()
    assert not domain.is_empty()

    config = await actual.get_config()
    assert config

    nlu_data = await actual.get_nlu_data()
    assert nlu_data.is_empty()


async def test_import_nlu_training_data_from_e2e_stories(project: Text):
    config_path = os.path.join(project, DEFAULT_CONFIG_PATH)
    domain_path = os.path.join(project, DEFAULT_DOMAIN_PATH)
    default_data_path = os.path.join(project, DEFAULT_DATA_PATH)
    importer = TrainingDataImporter.load_from_dict(
        {}, config_path, domain_path, [default_data_path]
    )

    # The `E2EImporter` correctly wraps the underlying `CombinedDataImporter`
    assert isinstance(importer, E2EImporter)
    importer_without_e2e = importer.importer

    stories = StoryGraph(
        [
            StoryStep(
                events=[
                    SlotSet("some slot", "doesn't matter"),
                    UserUttered("greet_from_stories", {"name": "greet_from_stories"}),
                    ActionExecuted("utter_greet_from_stories"),
                ]
            ),
            StoryStep(
                events=[
                    UserUttered("how are you doing?"),
                    ActionExecuted("utter_greet_from_stories", action_text="Hi Joey."),
                ]
            ),
        ]
    )

    # Patch to return our test stories
    importer_without_e2e.get_stories = asyncio.coroutine(lambda *args: stories)

    # The wrapping `E2EImporter` simply forwards these method calls
    assert (await importer_without_e2e.get_stories()).as_story_string() == (
        await importer.get_stories()
    ).as_story_string()
    assert (await importer_without_e2e.get_config()) == (await importer.get_config())

    # Check additional NLU training data from stories was added
    nlu_data = await importer.get_nlu_data()

    # The `E2EImporter` adds NLU training data based on our training stories
    assert len(nlu_data.training_examples) > len(
        (await importer_without_e2e.get_nlu_data()).training_examples
    )

    # Check if the NLU training data was added correctly from the story training data
    expected_additional_messages = [
        Message(data={TEXT: "greet_from_stories", INTENT_NAME: "greet_from_stories"}),
        Message(data={ACTION_NAME: "utter_greet_from_stories", ACTION_TEXT: ""}),
        Message(data={TEXT: "how are you doing?", INTENT_NAME: None}),
        Message(
            data={ACTION_NAME: "utter_greet_from_stories", ACTION_TEXT: "Hi Joey."}
        ),
    ]

    assert all(m in nlu_data.training_examples for m in expected_additional_messages)


async def test_import_nlu_training_data_with_default_actions(project: Text):
    config_path = os.path.join(project, DEFAULT_CONFIG_PATH)
    domain_path = os.path.join(project, DEFAULT_DOMAIN_PATH)
    default_data_path = os.path.join(project, DEFAULT_DATA_PATH)
    importer = TrainingDataImporter.load_from_dict(
        {}, config_path, domain_path, [default_data_path]
    )

    assert isinstance(importer, E2EImporter)
    importer_without_e2e = importer.importer

    # Check additional NLU training data from domain was added
    nlu_data = await importer.get_nlu_data()

    assert len(nlu_data.training_examples) > len(
        (await importer_without_e2e.get_nlu_data()).training_examples
    )

    extended_training_data = await importer.get_nlu_data()
    assert all(
        Message(data={ACTION_NAME: action_name, ACTION_TEXT: ""})
        in extended_training_data.training_examples
        for action_name in rasa.shared.core.constants.DEFAULT_ACTION_NAMES
    )


async def test_adding_e2e_actions_to_domain(project: Text):
    config_path = os.path.join(project, DEFAULT_CONFIG_PATH)
    domain_path = os.path.join(project, DEFAULT_DOMAIN_PATH)
    default_data_path = os.path.join(project, DEFAULT_DATA_PATH)
    existing = TrainingDataImporter.load_from_dict(
        {}, config_path, domain_path, [default_data_path]
    )

    additional_actions = ["Hi Joey.", "it's sunny outside."]
    stories = StoryGraph(
        [
            StoryStep(
                events=[
                    UserUttered("greet_from_stories", {"name": "greet_from_stories"}),
                    ActionExecuted("utter_greet_from_stories"),
                ]
            ),
            StoryStep(
                events=[
                    UserUttered("how are you doing?", {"name": "greet_from_stories"}),
                    ActionExecuted(
                        additional_actions[0], action_text=additional_actions[0]
                    ),
                    ActionExecuted(
                        additional_actions[1], action_text=additional_actions[1]
                    ),
                    ActionExecuted(
                        additional_actions[1], action_text=additional_actions[1]
                    ),
                ]
            ),
        ]
    )

    # Patch to return our test stories
    existing.get_stories = asyncio.coroutine(lambda *args: stories)

    importer = E2EImporter(existing)
    domain = await importer.get_domain()

    assert all(action_name in domain.action_names for action_name in additional_actions)


async def test_nlu_data_domain_sync_with_retrieval_intents(project: Text):
    config_path = os.path.join(project, DEFAULT_CONFIG_PATH)
    domain_path = "data/test_domains/default_retrieval_intents.yml"
    data_paths = [
        "data/test_nlu/default_retrieval_intents.md",
        "data/test_responses/default.md",
    ]
    base_data_importer = TrainingDataImporter.load_from_dict(
        {}, config_path, domain_path, data_paths
    )

    nlu_importer = NluDataImporter(base_data_importer)
    core_importer = CoreDataImporter(base_data_importer)

    importer = RetrievalModelsDataImporter(
        CombinedDataImporter([nlu_importer, core_importer])
    )
    domain = await importer.get_domain()
    nlu_data = await importer.get_nlu_data()

    assert domain.retrieval_intents == ["chitchat"]
    assert domain.intent_properties["chitchat"].get("is_retrieval_intent")
    assert domain.templates == nlu_data.responses
    assert "utter_chitchat" in domain.action_names
