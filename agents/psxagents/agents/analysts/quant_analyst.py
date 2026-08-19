from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from psxagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)
from psxagents.agents.utils.quant_forecast_tools import get_quant_forecast


def create_quant_analyst(llm):
    """The 'PSX TradingAgents' plan's Quant Analyst role: 'Not an LLM... Quant
    Forecast... Then the Quant Analyst interprets that.' Unlike the Equity Research
    Analyst (which relays a complete report verbatim), this analyst's job IS to
    interpret the real, numeric Kronos forecast into prose -- but it must not invent
    numbers of its own or override what the model actually said."""

    def quant_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        instrument_context = get_instrument_context_from_state(state)

        tools = [get_quant_forecast]

        system_message = (
            f"You are a quantitative analyst. Call `get_quant_forecast` with ticker="
            f'"{ticker}" to get a real, model-generated probabilistic price forecast '
            "(NOT an LLM output -- a genuine quantitative model run against real price "
            "history). Then write a short interpretation: what the probability of a "
            "positive return, expected return, downside VaR, volatility, and trend "
            "regime numbers imply for a trader, and how much weight the stated model "
            "confidence should carry. Report the real numbers you were given exactly "
            "as returned -- never invent, adjust, or round them to look more precise "
            "than they are. If the tool reports QUANT_FORECAST_UNAVAILABLE, relay that "
            "exact message and explain that no quantitative signal is available this run "
            "-- never substitute your own guessed forecast."
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
            "quant_report": report,
        }

    return quant_analyst_node
