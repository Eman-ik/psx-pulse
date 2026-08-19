from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from psxagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)
from psxagents.agents.utils.equity_research_tools import get_equity_research_report


def create_equity_research_analyst(llm):
    """Bridges in the Equity-research project's real, deterministic 8-agent pipeline
    as a single analyst: it does not re-derive an assessment itself, it relays the
    real, already-verified report Equity-research published for this ticker (or an
    honest not-covered/unavailable message -- see equity_research_tools.py). Kept as
    a single-tool LLM node (not a raw deterministic lookup) so it wires into the
    existing analyst_execution.py / conditional_logic.py machinery unchanged."""

    def equity_research_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        instrument_context = get_instrument_context_from_state(state)

        tools = [get_equity_research_report]

        system_message = (
            f"You have exactly one job: call `get_equity_research_report` with ticker="
            f'"{ticker}" ONCE, then relay its content back verbatim as your report -- do '
            "not summarize, shorten, paraphrase, or add your own analysis on top of it. "
            "This report comes from a separate, already-verified, citation-grounded "
            "research pipeline; your role is to carry it into this team's discussion "
            "intact, not to reinterpret it. If the tool reports the ticker is "
            "NOT_COVERED or the database is EQUITY_RESEARCH_UNAVAILABLE, relay that "
            "exact message as your report -- never invent a substitute assessment."
            + get_language_instruction(),
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}."
                    " Today's date is {current_date}; treat it as 'now' for all analysis and tool-call date ranges. {instrument_context}\n"
                    "{system_message}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(instrument_context=instrument_context)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "equity_research_report": report,
        }

    return equity_research_analyst_node
