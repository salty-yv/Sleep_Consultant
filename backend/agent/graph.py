"""
LangGraph 状态图组装（Phase 2+3 完整版）
节点顺序：input_parser → memory_retrieval → react_agent → [条件路由] → action_executor / memory_updater → END
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent.state import AgentState
from agent.nodes.input_parser import input_parser_node
from agent.nodes.memory_retrieval import memory_retrieval_node
from agent.nodes.react_agent import react_agent_node
from agent.nodes.action_executor import action_executor_node
from agent.nodes.memory_updater import memory_updater_node


def _should_execute_actions(state: AgentState) -> str:
    """条件路由：有推荐 IoT 动作时走 action_executor，否则直接到 memory_updater"""
    if state.recommended_actions:
        return "action_executor"
    return "memory_updater"


def build_graph():
    """构造并编译 SleepMind Agent 状态图（完整版）"""
    builder = StateGraph(AgentState)

    # 注册节点
    builder.add_node("input_parser", input_parser_node)
    builder.add_node("memory_retrieval", memory_retrieval_node)
    builder.add_node("react_agent", react_agent_node)
    builder.add_node("action_executor", action_executor_node)
    builder.add_node("memory_updater", memory_updater_node)

    # 边
    builder.add_edge(START, "input_parser")
    builder.add_edge("input_parser", "memory_retrieval")
    builder.add_edge("memory_retrieval", "react_agent")

    # 条件路由：Agent 推荐了 IoT 动作 → 执行 → 写记忆
    builder.add_conditional_edges("react_agent", _should_execute_actions, {
        "action_executor": "action_executor",
        "memory_updater": "memory_updater",
    })
    builder.add_edge("action_executor", "memory_updater")
    builder.add_edge("memory_updater", END)

    return builder.compile()


# 全局单例
sleep_agent = build_graph()
