"""
A2A Travel Booking Agent Client

Walks through the complete A2A task lifecycle:
  1. Discovery   -- fetch the agent card
  2. First turn  -- send "Book a flight to Paris" -> INPUT_REQUIRED
  3. Second turn -- provide dates                 -> COMPLETED (with artifact)
  4. Retrieval   -- fetch the final task state
  5. New task    -- book a hotel (same context, new task)

Uses the official a2a-sdk Python package.
"""

import asyncio
import logging
import warnings

import httpx

from a2a.client import A2AClient
from a2a.types import (
    Message,
    MessageSendConfiguration,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    Task,
    TaskQueryParams,
    GetTaskRequest,
    TextPart,
)
from uuid import uuid4

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

AGENT_URL = "http://localhost:9999"


def get_result(response):
    """Unwrap the result from a SendMessageResponse."""
    return response.root.result if hasattr(response, "root") else response.result


def print_task_info(result) -> None:
    """Print task state and agent reply from a Task result."""
    if isinstance(result, Task):
        print(f"  Task ID       : {result.id}")
        print(f"  Context ID    : {result.context_id}")
        print(f"  Task State    : {result.status.state.value}")
        if result.status.message and result.status.message.parts:
            for part in result.status.message.parts:
                p = part.root if hasattr(part, "root") else part
                if hasattr(p, "text"):
                    print(f"  Agent Reply   : {p.text}")
        if result.artifacts:
            print(f"\n  Artifacts ({len(result.artifacts)}):")
            for i, artifact in enumerate(result.artifacts):
                print(f"\n  --- Artifact {i + 1} ---")
                if artifact.parts:
                    for part in artifact.parts:
                        p = part.root if hasattr(part, "root") else part
                        if hasattr(p, "text"):
                            for line in p.text.split("\n"):
                                print(f"  {line}")
    elif isinstance(result, Message):
        print(f"  (Received a Message, not a Task)")
        if result.parts:
            for part in result.parts:
                p = part.root if hasattr(part, "root") else part
                if hasattr(p, "text"):
                    print(f"  Agent Reply   : {p.text}")


async def main():
    print("\n  A2A Travel Booking Agent -- Client Demo")
    print("  ========================================\n")

    async with httpx.AsyncClient() as httpx_client:

        # ------------------------------------------------------------------
        # Step 1: Discovery -- Fetch the Agent Card
        # ------------------------------------------------------------------
        # Note: A2AClient is the simpler JSON-RPC client. The newer
        # ClientFactory/Client API supports streaming and advanced features
        # but is more complex. For non-streaming demos, A2AClient works well.
        warnings.filterwarnings("ignore", message="A2AClient is deprecated")
        client = A2AClient(httpx_client=httpx_client, url=AGENT_URL)
        card = await client.get_card()

        print(f"\n  Step 1: Discovery")
        print("  " + "-" * 38)
        print(f"  Agent Name    : {card.name}")
        print(f"  Description   : {card.description}")
        print(f"  URL           : {card.url}")
        print(f"  Skills        : {[s.name for s in card.skills]}")
        print(f"  Streaming     : {card.capabilities.streaming}")
        print(f"  Push Notifs   : {card.capabilities.push_notifications}")

        # We use a shared context_id so the server knows
        # these messages belong to the same conversation.
        context_id = uuid4().hex

        # ------------------------------------------------------------------
        # Step 2: First Turn -- "Book a flight to Paris"
        # ------------------------------------------------------------------
        print("\n  Step 2: Send Initial Message")
        print("  " + "-" * 38)
        first_message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text="Book a flight to Paris"))],
            message_id=uuid4().hex,
            context_id=context_id,
        )

        request1 = SendMessageRequest(
            id=uuid4().hex,
            params=MessageSendParams(
                message=first_message,
                configuration=MessageSendConfiguration(
                    accepted_output_modes=["text"],
                ),
            )
        )

        print("  Sending: 'Book a flight to Paris'")
        response1 = await client.send_message(request1)
        result1 = get_result(response1)
        print_task_info(result1)

        # Extract task_id for the follow-up turn
        task_id = result1.id if isinstance(result1, Task) else None

        if isinstance(result1, Task) and result1.status.state.value == "input-required":
            print("\n  -> The agent needs more information (INPUT_REQUIRED).")
            print("     This is the multi-turn handshake in action!")

        # ------------------------------------------------------------------
        # Step 3: Second Turn -- Provide travel dates
        # ------------------------------------------------------------------
        print("\n  Step 3: Provide Additional Input (Multi-Turn)")
        print("  " + "-" * 38)
        second_message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text="June 15 - June 22, 2026"))],
            message_id=uuid4().hex,
            context_id=context_id,
            task_id=task_id,  # <-- reference the existing task
        )

        request2 = SendMessageRequest(
            id=uuid4().hex,
            params=MessageSendParams(
                message=second_message,
                configuration=MessageSendConfiguration(
                    accepted_output_modes=["text"],
                ),
            )
        )

        print("  Sending: 'June 15 - June 22, 2026'")
        response2 = await client.send_message(request2)
        result2 = get_result(response2)
        print_task_info(result2)

        if isinstance(result2, Task) and result2.status.state.value == "completed":
            print("\n  -> Task COMPLETED successfully!")

        # ------------------------------------------------------------------
        # Step 4: Retrieve Task (verify final state)
        # ------------------------------------------------------------------
        print("\n  Step 4: Retrieve Task (Verify Final State)")
        print("  " + "-" * 38)
        try:
            get_request = GetTaskRequest(
                id=uuid4().hex,
                params=TaskQueryParams(id=task_id)
            )
            task_response = await client.get_task(get_request)
            task_result = get_result(task_response)

            print(f"  Task ID       : {task_result.id}")
            print(f"  Context ID    : {task_result.context_id}")
            print(f"  Final State   : {task_result.status.state.value}")

            if task_result.artifacts:
                print(f"  Artifacts     : {len(task_result.artifacts)} attached")
        except Exception as e:
            print(f"  (get_task not available or failed: {e})")

        # ------------------------------------------------------------------
        # Step 5: New Task in Same Context -- "Book a hotel"
        # ------------------------------------------------------------------
        # The flight task is COMPLETED (terminal, immutable).
        # By sending a message with the SAME context_id but NO task_id,
        # we create a brand-new task within the same conversation.
        print("\n  Step 5: New Task in Same Context")
        print("  " + "-" * 38)

        hotel_message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(
                text="Book a hotel near the airport in Paris"
            ))],
            message_id=uuid4().hex,
            context_id=context_id,  # <-- same context as the flight task
            # NOTE: no task_id — this creates a NEW task
        )

        request3 = SendMessageRequest(
            id=uuid4().hex,
            params=MessageSendParams(
                message=hotel_message,
                configuration=MessageSendConfiguration(
                    accepted_output_modes=["text"],
                ),
            )
        )

        print("  Sending: 'Book a hotel near the airport in Paris'")
        response3 = await client.send_message(request3)
        result3 = get_result(response3)
        print_task_info(result3)

        hotel_task_id = result3.id if isinstance(result3, Task) else None

        if isinstance(result3, Task) and result3.status.state.value == "completed":
            print("\n  -> New task COMPLETED in the same context!")

        # ------------------------------------------------------------------
        # Summary
        # ------------------------------------------------------------------
        print("\n  Context & Task Summary")
        print("  " + "=" * 38)
        print(f"  Context ID    : {context_id}")
        print(f"  Task 1 (Flight): {task_id}")
        print(f"  Task 2 (Hotel) : {hotel_task_id}")
        print("  Both tasks share the same context,")
        print("  but each has its own lifecycle.")
        print()


if __name__ == "__main__":
    asyncio.run(main())
