from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mcp-anki")

class Flashcard:
    def __init__(self, 
                deck_name: str = "Default Deck", 
                model_name: str = "Basic", 
                tags: list[str] = None, 
                front: str = "Default Front", 
                back: str = "Default Back"):
        if tags is None:  # Avoid mutable default arguments
            tags = []
        if "ai-generated" not in tags:
            tags.append("ai-generated")
        self.action = "addNote"
        self.params = {
            "note": {
                "deckName": deck_name,
                "modelName": model_name,
                "tags": tags,
                "fields": {
                    "Front": front,
                    "Back": back
                }
            }
        }

async def make_ankiconnect_request(request_params):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://localhost:8765", json=request_params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            return f"Request failed: {str(e)}"
        
@mcp.tool()
async def get_decks() -> str:
    """ Holt alle Decks von Anki.
        Dient dazu, dass man schauen kann, ob es schon einen Stapel, der zu dem Thema passt gibt.
    """
    request_params = {
        "action": "deckNames",
        "version": 6
    }
    data = await make_ankiconnect_request(request_params=request_params)
    if data and data.get("error") is None:
        return f"Namen von den Decks: {data.get('result')}"
    else:
        return f"Fehler beim Abrufen der Deck-Namen: {data.get('error')}"



@mcp.tool()
async def create_deck(name: str) -> None:
    """ Erstellt ein neues Deck.
        Soll nur verwendet werden, nachdem mit `get_decks` getestet wird, ob es nicht schon einen passenden gibt.

        Args:
            name: Name von dem neuen Deck
    """
    request_params={
        "action": "createDeck",
        "version": 6,
        "params": {
            "deck": name
        }
    }
    data = await make_ankiconnect_request(request_params=request_params)
    if data and data.get("error") is None:
        return f"Stapel {name} wurde erfolgreich erstellt"
    else:
        return f"Fehler beim Erstellen von Stapel {name}"

@mcp.tool()
async def create_flashcard(front: str, back: str, tags: list[str], deck_name: str) -> None:
    """ Erstellt eine neue Flashcard. Das verwendete Programm ist anki, dementsprechen ist formattierung mit HTML erwünscht, wenn es sinnvoll ist.
        Hightlighte wichtigen Text auf diese Weise z.B. als Bold, stell Stichpunkte als List-Items dar etc.
    
        Args:
            front: Vorderseite der Flashcard, also z.B. Fragestellung
            back: Rückseite der Flashcard, also Antwort
            tags: Inhaltliche Tags zu den Karten
            deck_name: Name des Decks
    """
    flashcard = Flashcard(
        front=front,
        back=back,
        tags=tags,
        deck_name=deck_name
    )

    data = await make_ankiconnect_request(request_params=flashcard.__dict__)
    if data:
        return f"Karte `{front}` wurde erfolgreich erstellt"
    else:
        return f"Fehler beim Erstellen von Karte \n`{flashcard.__dict__}`"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
