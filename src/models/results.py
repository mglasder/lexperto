from pydantic import BaseModel, Field


class RulingsResearchResult(BaseModel):
    """Enthält das Ergebnise einer Recherche in  Urteilen in Amtshilfeverfahren."""

    analysis: list[str] = Field(
        default=[],
        description="Analyse des Rechercheergebnisses, für jede Fragestellung.",
    )
    examples: list[str] = Field(
        default=[],
        description="Formulierungsbeispiele für jeden zu recherchierende Fragestellung.",
    )

    def get_as_text(self) -> str:
        """Gibt die Ergebnisse als Text zurück."""
        result = []
        for i, analysis in enumerate(self.analysis):
            result.append(f"Analyse zu Frage {i + 1}:\n{analysis}\n")
        for i, example in enumerate(self.examples):
            result.append(f"Formulierungsbeispiel zu {i + 1}:\n{example}\n")
        return "\n".join(result)
