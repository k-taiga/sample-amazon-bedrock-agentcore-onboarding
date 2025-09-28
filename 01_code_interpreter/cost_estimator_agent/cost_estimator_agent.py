"""
Amazon Bedrock AgentCore Code Interpreterを使用したAWSコスト見積もりエージェント

このエージェントは以下を実証します：
1. AWS Pricing MCP Serverを使用して価格データを取得
2. セキュアな計算のためのAgentCore Code Interpreterの使用
3. AWSアーキテクチャの包括的なコスト見積もりの提供

主な機能：
- AgentCoreサンドボックスでのセキュアなコード実行
- リアルタイムAWS価格データ
- 包括的なロギングとエラーハンドリング
- 段階的な複雑性の構築
"""

import logging
import traceback
import boto3
from contextlib import contextmanager
from typing import Generator, AsyncGenerator
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from strands.handlers.callback_handler import null_callback_handler
from botocore.config import Config
from mcp import stdio_client, StdioServerParameters
from bedrock_agentcore.tools.code_interpreter_client import CodeInterpreter
from cost_estimator_agent.config import (
    SYSTEM_PROMPT,
    COST_ESTIMATION_PROMPT,
    DEFAULT_MODEL,
    LOG_FORMAT
)

# デバッグとモニタリングのための包括的なロギング設定
logging.basicConfig(
    level=logging.ERROR,  # デフォルトはERROR、詳細が必要な場合はDEBUGに変更可能
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler()]
)

# エージェントの詳細な動作確認用のStrandsデバッグロギングを有効化
logging.getLogger("strands").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


class AWSCostEstimatorAgent:
    """
    AgentCore Code Interpreterを使用したAWSコスト見積もりエージェント
    
    このエージェントは以下を組み合わせます：
    - リアルタイム価格データ用のMCP価格ツール（自動的に利用可能）
    - セキュアな計算用のAgentCore Code Interpreter
    - クリーンな実装のためのStrands Agentsフレームワーク
    """
    
    def __init__(self, region: str = ""):
        """
        コスト見積もりエージェントを初期化
        
        引数:
            region: AgentCore Code Interpreter用のAWSリージョン
        """
        self.region = region
        if not self.region:
            # 指定されていない場合はboto3セッションからデフォルトリージョンを使用
            self.region = boto3.Session().region_name
        self.code_interpreter = None
        
        logger.info(f"AWSコスト見積もりエージェントを初期化中（リージョン: {region}）")

    def _setup_code_interpreter(self) -> None:
        """安全な計算のためのAgentCore Code Interpreterをセットアップ"""
        try:
            logger.info("AgentCore Code Interpreterをセットアップ中...")
            self.code_interpreter = CodeInterpreter(self.region)
            self.code_interpreter.start()
            logger.info("✅ AgentCore Code Interpreterセッションが正常に開始されました")
        except Exception as e:
            logger.exception(f"❌ Code Interpreterのセットアップに失敗しました: {e}")
            raise
    
    def _get_aws_credentials(self) -> dict:
        """
        現在のAWS認証情報を取得（セッショントークンが存在する場合は含む）
        
        戻り値:
            セッショントークンを含む現在のAWS認証情報の辞書
        """
        try:
            logger.info("現在のAWS認証情報を取得中...")
            
            # 現在の認証情報を取得するためのセッションを作成
            session = boto3.Session()
            credentials = session.get_credentials()
            
            if credentials is None:
                raise Exception("AWS認証情報が見つかりません")
            
            # 呼び出し元のIDを取得して認証情報が機能することを確認
            sts_client = boto3.client('sts', region_name=self.region)
            identity = sts_client.get_caller_identity()
            logger.info(f"使用中のAWSアイデンティティ: {identity.get('Arn', '不明')}")
            
            # アクセスするために凍結された認証情報を取得
            frozen_creds = credentials.get_frozen_credentials()
            
            credential_dict = {
                "AWS_ACCESS_KEY_ID": frozen_creds.access_key,
                "AWS_SECRET_ACCESS_KEY": frozen_creds.secret_key,
                "AWS_REGION": self.region
            }
            
            # 利用可能な場合はセッショントークンを追加（EC2インスタンスロールがこれを提供）
            if frozen_creds.token:
                credential_dict["AWS_SESSION_TOKEN"] = frozen_creds.token
                logger.info("✅ セッショントークン付きのAWS認証情報を使用中（おそらくEC2インスタンスロールから）")
            else:
                logger.info("✅ セッショントークンなしのAWS認証情報を使用中")
                
            return credential_dict
            
        except Exception as e:
            logger.error(f"❌ AWS認証情報の取得に失敗しました: {e}")
            return {}  # フォールバックとして空の辞書を返す

    def _setup_aws_pricing_client(self) -> MCPClient:
        """現在のAWS認証情報でAWS Pricing MCP Clientをセットアップ"""
        try:
            logger.info("AWS Pricing MCP Clientをセットアップ中...")
            
            # 現在の認証情報を取得（利用可能な場合はセッショントークンを含む）
            aws_credentials = self._get_aws_credentials()
            
            # MCPクライアント用の環境変数を準備
            env_vars = {
                "FASTMCP_LOG_LEVEL": "ERROR",
                **aws_credentials  # すべてのAWS認証情報を含める
            }
            
            aws_pricing_client = MCPClient(
                lambda: stdio_client(StdioServerParameters(
                    command="uvx", 
                    args=["awslabs.aws-pricing-mcp-server@latest"],
                    env=env_vars
                ))
            )
            logger.info("✅ AWS Pricing MCP ClientがAWS認証情報で正常にセットアップされました")
            return aws_pricing_client
        except Exception as e:
            logger.error(f"❌ AWS Pricing MCP Clientのセットアップに失敗しました: {e}")
            return None  # フォールバックとしてNoneを返す

    # @tool = この関数をAIツールとして登録
    @tool
    def execute_cost_calculation(self, calculation_code: str, description: str = "") -> str:
        """AgentCore Code Interpreterを使用してコスト計算を実行"""
        if not self.code_interpreter:
            return "❌ Code Interpreterが初期化されていません"

        try:
            # セキュアなAgentCoreサンドボックスでコードを実行
            response = self.code_interpreter.invoke("executeCode", {
                "language": "python",
                "code": calculation_code
            })

            # レスポンスストリームから結果を抽出
            results = []
            for event in response.get("stream", []):
                if "result" in event:
                    result = event["result"]
                    if "content" in result:
                        for content_item in result["content"]:
                            if content_item.get("type") == "text":
                                results.append(content_item["text"])

            return "\n".join(results)
        except Exception as e:
            logger.exception(f"❌ 計算に失敗しました: {e}")

    # withで使える便利な関数にする
    @contextmanager
    def _estimation_agent(self) -> Generator[Agent, None, None]:
        """コスト見積もりコンポーネントのコンテキストマネージャー"""
        try:
            # コンポーネントを順番にセットアップ
            self._setup_code_interpreter()
            aws_pricing_client = self._setup_aws_pricing_client()

            # execute_cost_calculationとMCP料金ツールの両方でエージェントを作成
            with aws_pricing_client:
                pricing_tools = aws_pricing_client.list_tools_sync()
                all_tools = [self.execute_cost_calculation] + pricing_tools
                agent = Agent(
                    model=DEFAULT_MODEL,
                    tools=all_tools,
                    system_prompt=SYSTEM_PROMPT
                )
                yield agent
        finally:
            # 成功/失敗に関わらずクリーンアップを確実に実行
            self.cleanup()

    def estimate_costs(self, architecture_description: str) -> str:
        """
        指定されたアーキテクチャの説明に対するコストを見積もる
        
        引数:
            architecture_description: 見積もり対象のシステムの説明
            
        戻り値:
            連結された文字列としてのコスト見積もり結果
        """
        logger.info("📊 コスト見積もりを開始中...")
        logger.info(f"アーキテクチャ: {architecture_description}")
        
        try:
            with self._estimation_agent() as agent:
                # エージェントを使用してコスト見積もりリクエストを処理
                prompt = COST_ESTIMATION_PROMPT.format(
                    architecture_description=architecture_description
                )
                result = agent(prompt)
                
                logger.info("✅ コスト見積もりが完了しました")

                if result.message and result.message.get("content"):
                    # すべてのContentBlocksからテキストを抽出して連結
                    text_parts = []
                    for content_block in result.message["content"]:
                        if isinstance(content_block, dict) and "text" in content_block:
                            text_parts.append(content_block["text"])
                    return "".join(text_parts) if text_parts else "テキストコンテンツが見つかりません。"
                else:
                    return "見積もり結果がありません。"

        except Exception as e:
            logger.exception(f"❌ コスト見積もりに失敗しました: {e}")
            error_details = traceback.format_exc()
            return f"❌ コスト見積もりに失敗しました: {e}\n\nスタックトレース:\n{error_details}"

    async def estimate_costs_stream(self, architecture_description: str) -> AsyncGenerator[dict, None]:
        """適切なデルタハンドリングでコスト見積もりをストリーミング"""
        try:
            with self._estimation_agent() as agent:
                # ストリーミングでコスト見積もりリクエストを処理
                prompt = COST_ESTIMATION_PROMPT.format(
                    architecture_description=architecture_description
                )

                logger.info("🔄 コスト見積もりレスポンスをストリーミング中...")

                # 重複を防ぐための適切なデルタハンドリングを実装
                previous_output = ""

                agent_stream = agent.stream_async(prompt, callback_handler=null_callback_handler)

                async for event in agent.stream_async(prompt, callback_handler=null_callback_handler):
                    if "data" in event:
                        current_chunk = str(event["data"])

                        # Bedrockのベストプラクティスに従ってデルタ計算を処理
                        if current_chunk.startswith(previous_output):
                            # 新しい部分のみを抽出
                            delta_content = current_chunk[len(previous_output):]
                            if delta_content:
                                previous_output = current_chunk
                                yield {"data": delta_content}
                        else:
                            # 完全に新しいチャンクまたはリセット - そのまま出力
                            previous_output = current_chunk
                            yield {"data": current_chunk}
                    else:
                        # データ以外のイベント（エラー、メタデータなど）をそのまま通す
                        yield event

                logger.info("✅ ストリーミングコスト見積もりが完了しました")

        except Exception as e:
            logger.exception(f"❌ ストリーミングコスト見積もりに失敗しました: {e}")
            # ストリーミング形式でエラーイベントを出力
            yield {
                "error": True,
                "data": f"❌ ストリーミングコスト見積もりに失敗しました: {e}\n\nスタックトレース:\n{traceback.format_exc()}"
            }

    def cleanup(self) -> None:
        """リソースをクリーンアップ"""
        logger.info("🧹 リソースをクリーンアップ中...")
        
        if self.code_interpreter:
            try:
                self.code_interpreter.stop()
                logger.info("✅ Code Interpreterセッションが停止しました")
            except Exception as e:
                logger.warning(f"⚠️ Code Interpreterの停止中にエラーが発生: {e}")
            finally:
                self.code_interpreter = None
