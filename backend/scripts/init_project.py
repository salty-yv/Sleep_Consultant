"""
项目初始化脚本
运行一次即可：创建数据库表 + 初始化 ChromaDB 知识库

用法：
  cd e:\Sleep_Consultant\backend
  python scripts/init_project.py
"""
import asyncio
import sys
import os

# 把 backend 目录加入 PATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def step1_create_tables():
    print("\n── Step 1: 创建 PostgreSQL 数据库表 ──────────────")
    try:
        from db.database import init_db
        await init_db()
        print("✅  数据库表创建成功（users, sleep_records）")
    except Exception as e:
        print(f"❌  数据库创建失败：{e}")
        print("    请确认 PostgreSQL 已启动，且数据库 sleepmind 已创建")
        print("    创建命令（在 pgAdmin 或 SQL 客户端执行）：CREATE DATABASE sleepmind;")
        raise


def step2_ingest_knowledge():
    print("\n── Step 2: 初始化 ChromaDB 知识库 ─────────────────")
    try:
        from rag.ingest import ingest_knowledge_base
        ingest_knowledge_base()
    except Exception as e:
        print(f"❌  知识库初始化失败：{e}")
        raise


def step3_verify():
    print("\n── Step 3: 验证指标计算逻辑 ────────────────────────")
    try:
        import pandas as pd
        from data.parser import parse_csv_to_session
        from data.metrics import compute_metrics

        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "new_data_with_pred.csv"
        )
        if not os.path.exists(csv_path):
            print(f"⚠️  未找到 {csv_path}，跳过验证")
            return

        df = pd.read_csv(csv_path)
        session = parse_csv_to_session(df, user_id="u001", date="2026-03-11")
        metrics = compute_metrics(session)

        print(f"✅  CSV 解析成功：共 {session.total_epochs} 个 epoch（{session.total_duration_min:.0f} 分钟）")
        print(f"   睡眠时长：{metrics.total_sleep_min:.0f} 分钟")
        print(f"   REM    ：{metrics.rem_pct:.1f}%  （标准 20-25%，{'⚠️ 偏低' if metrics.rem_pct < 20 else '✅ 正常'}）")
        print(f"   深睡   ：{metrics.deep_pct:.1f}%  （标准 15-20%，{'⚠️ 偏低' if metrics.deep_pct < 15 else '✅ 正常'}）")
        print(f"   效率   ：{metrics.sleep_efficiency_pct:.1f}%  （{'⚠️ 偏低' if metrics.sleep_efficiency_pct < 85 else '✅ 正常'}）")
        print(f"   觉醒   ：{metrics.awakening_count} 次")
        print(f"   周期   ：{metrics.sleep_cycle_count} 个")
        print(f"   平均心率：{metrics.avg_hr} bpm")
    except Exception as e:
        print(f"❌  验证失败：{e}")
        raise


async def main():
    print("🚀 SleepMind 项目初始化开始...")
    await step1_create_tables()
    step2_ingest_knowledge()
    step3_verify()
    print("\n" + "="*55)
    print("🎉  初始化完成！现在可以启动服务：")
    print("    cd e:\\Sleep_Consultant\\backend")
    print("    uvicorn main:app --reload --port 8000")
    print("    API 文档：http://localhost:8000/docs")
    print("="*55)


if __name__ == "__main__":
    asyncio.run(main())
