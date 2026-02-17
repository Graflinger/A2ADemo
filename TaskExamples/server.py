"""
A2A Travel Booking Agent Server

Demonstrates the full A2A task lifecycle including multiple tasks per context:
  Task 1: SUBMITTED -> WORKING -> INPUT_REQUIRED -> WORKING -> COMPLETED
  Task 2: SUBMITTED -> WORKING -> COMPLETED  (new task, same context)

Uses the official a2a-sdk Python package.
"""

import logging
import uvicorn

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.server.apps import A2AStarletteApplication
from a2a.types import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    Part,
    TextPart,
)
from a2a.utils import new_agent_text_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Agent logic (no A2A dependency — pure business logic)
# ---------------------------------------------------------------------------

class TravelAgent:
    """Simple travel booking agent that requires multi-turn conversation."""

    async def process(self, user_input: str, context_id: str) -> dict:
        """
        Returns a dict with:
          - response: str        text reply
          - needs_input: bool    whether additional user input is required
          - booking: dict | None booking confirmation details (when complete)
        """
        text = user_input.lower()

        # ---- Hotel booking (new task in same context) ----
        if "hotel" in text:
            return {
                "response": (
                    "Your hotel has been booked! Here are the details:"
                ),
                "needs_input": False,
                "booking": {
                    "type": "Hotel",
                    "hotel": "Le Ciel Paris Airport",
                    "location": "Near Charles de Gaulle Airport, Paris",
                    "check_in": "June 15, 2026",
                    "check_out": "June 22, 2026",
                    "room": "Deluxe King",
                    "status": "CONFIRMED",
                },
            }

        # ---- Flight booking: second turn (dates provided) ----
        has_date = any(
            date in text
            for date in [
                "jan", "feb", "mar", "apr", "may", "jun",
                "jul", "aug", "sep", "oct", "nov", "dec",
                "2025", "2026", "2027",
            ]
        )

        if has_date:
            return {
                "response": (
                    "Your flight has been booked! Here are the details:"
                ),
                "needs_input": False,
                "booking": {
                    "type": "Flight",
                    "destination": "Paris",
                    "departure": user_input.strip(),
                    "airline": "SkyHigh Airlines",
                    "flight": "SH-1042",
                    "status": "CONFIRMED",
                },
            }

        # ---- Flight booking: first turn (no dates yet) ----
        return {
            "response": (
                "I'd be happy to help you book a flight! "
                "Could you please provide your preferred travel dates? "
                "(e.g. 'June 15 - June 22, 2026')"
            ),
            "needs_input": True,
            "booking": None,
        }


# ---------------------------------------------------------------------------
# A2A Agent Executor (bridges protocol <-> business logic)
# ---------------------------------------------------------------------------

class TravelAgentExecutor(AgentExecutor):
    """
    Handles incoming A2A requests for the Travel Booking Agent.

    Lifecycle demonstrated:
      1st message  -> SUBMITTED -> WORKING -> INPUT_REQUIRED
      2nd message  -> WORKING -> COMPLETED  (with artifact)
    """

    def __init__(self):
        self.agent = TravelAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        # Extract the user's text input from the request context
        user_input = context.get_user_input()
        if not user_input:
            user_input = ""

        # Get or create a task
        task = context.current_task

        # Create a TaskUpdater to manage state transitions
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        if not task:
            # Brand-new task — submit it first
            await updater.submit()
            logger.info(
                "Task %s: SUBMITTED (context=%s)",
                context.task_id,
                context.context_id,
            )

        # Transition to WORKING
        await updater.start_work()
        logger.info("Task %s: WORKING", context.task_id)

        # Run the agent's business logic
        result = await self.agent.process(user_input, context.context_id)

        if result["needs_input"]:
            # Agent needs more information from the user
            await updater.requires_input(
                new_agent_text_message(
                    result["response"],
                    context.context_id,
                    context.task_id,
                ),
            )
            logger.info("Task %s: INPUT_REQUIRED", context.task_id)
        else:
            # Agent has completed the task — attach booking as artifact
            booking = result["booking"]
            if booking.get("type") == "Hotel":
                artifact_text = (
                    f"Booking Confirmation\n"
                    f"====================\n"
                    f"Type        : {booking['type']}\n"
                    f"Hotel       : {booking['hotel']}\n"
                    f"Location    : {booking['location']}\n"
                    f"Check-in    : {booking['check_in']}\n"
                    f"Check-out   : {booking['check_out']}\n"
                    f"Room        : {booking['room']}\n"
                    f"Status      : {booking['status']}"
                )
            else:
                artifact_text = (
                    f"Booking Confirmation\n"
                    f"====================\n"
                    f"Type        : {booking['type']}\n"
                    f"Destination : {booking['destination']}\n"
                    f"Dates       : {booking['departure']}\n"
                    f"Airline     : {booking['airline']}\n"
                    f"Flight      : {booking['flight']}\n"
                    f"Status      : {booking['status']}"
                )

            # Attach the structured booking artifact
            await updater.add_artifact(
                parts=[Part(root=TextPart(text=artifact_text))],
            )

            # Mark task as completed with response message
            await updater.complete(
                new_agent_text_message(
                    result["response"],
                    context.context_id,
                    context.task_id,
                ),
            )
            logger.info("Task %s: COMPLETED", context.task_id)

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel()
        logger.info("Task %s: CANCELED", context.task_id)


# ---------------------------------------------------------------------------
# Server bootstrap
# ---------------------------------------------------------------------------

def build_agent_card() -> AgentCard:
    """Construct the AgentCard that describes this agent's capabilities."""
    skill = AgentSkill(
        id="travel_booking",
        name="Travel Booking",
        description=(
            "Books flights and hotels for destinations worldwide. "
            "Supports multi-turn conversations to collect travel details."
        ),
        tags=["travel", "flights", "hotels", "booking"],
        examples=[
            "Book a flight to Paris",
            "I need a flight to Tokyo next month",
            "Book a hotel near the airport",
        ],
    )

    return AgentCard(
        name="Travel Booking Agent",
        description=(
            "An AI-powered travel agent that helps you book flights and hotels. "
        ),
        url="http://localhost:9999",
        version="1.0.0",
        skills=[skill],
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(
            streaming=False,
            pushNotifications=False,
        ),
    )


if __name__ == "__main__":
    agent_card = build_agent_card()

    request_handler = DefaultRequestHandler(
        agent_executor=TravelAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app_builder = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    print("\n  Travel Booking Agent (A2A Server)")
    print("  Agent Card : http://localhost:9999/.well-known/agent-card.json")
    print("  Endpoint   : http://localhost:9999/")

    uvicorn.run(app_builder.build(), host="0.0.0.0", port=9999)
