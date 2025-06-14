import json
import shutil
from pathlib import Path

import yaml
import pytest
from models import SectionName, MetaData, Paragraph, Section, CourtDecision
import os


@pytest.fixture(scope="function")
def temp_folder(tmpdir):
    """Creates a temporary folder, yields its path, and removes it after the test."""
    temp_folder_path = Path(tmpdir)
    yield temp_folder_path
    shutil.rmtree(temp_folder_path)


def test_models_creation_saving_parsing(temp_folder):

    os.makedirs("test_temp", exist_ok=True)

    decision = CourtDecision(
        meta=MetaData(
            aktenzeichen="1234/5678",
            entscheid_datum="2023-10-01",
            publikations_datum="2023-10-02",
            eingangsjahr="2023",
            abteilung="Abteilung A",
            sprache="Deutsch",
            gegenstand="Gegenstand A",
            gerichtsschreiber=["Schreiber 1", "Schreiber 2"],
            richter=["Richter 1", "Richter 2"],
            parteien=["Partei A", "Partei B"],
            zitierte_gesetze=["Gesetz A", "Gesetz B"],
            zitierte_entscheide=["Entscheid A", "Entscheid B"],
            stichworte=["Stichwort A", "Stichwort B"],
        ),
        content=[
            Section(
                name=SectionName.SACHVERHALT,
                content=[
                    Paragraph(
                        number="1.",
                        text="Sachverhalt Text 1",
                        subparagraphs=[
                            Paragraph(number="1.1", text="Sachverhalt Text 1.1"),
                            Paragraph(number="1.2", text="Sachverhalt Text 1.2"),
                        ],
                    ),
                ],
            ),
            Section(
                name=SectionName.ERWAEGUNGEN,
                content=[Paragraph(number="2.", text="Erwaegungen Text 2")],
            ),
        ],
    )

    # Save to YAML
    yaml_path = os.path.join("test_temp", "decision.yaml")
    with open(yaml_path, "w", encoding="utf-8") as yaml_file:
        yaml_file.write(decision.to_yaml())

    # Save to JSON
    json_path = os.path.join("test_temp", "decision.json")
    with open(json_path, "w", encoding="utf-8") as json_file:
        json_file.write(decision.to_json())

    loaded_decision_yaml = CourtDecision.from_yaml_file(yaml_path)
    loaded_decision = CourtDecision.from_json_file(json_path)

    assert decision == loaded_decision, "json loaded decision does not match original"
    assert (
        decision == loaded_decision_yaml
    ), "yaml loaded decision does not match original"
    assert loaded_decision.meta.aktenzeichen == "1234/5678", "Aktenzeichen mismatch"
    assert loaded_decision.content[0].name == "sachverhalt", "section name mismatch"
    assert (
        loaded_decision.content[0].content[0].text == "Sachverhalt Text 1"
    ), "Paragraph text mismatch"
