"""Backend tools used by the CloudPulse agent."""

from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    text: str
    source_url: str
    title: str = ""
