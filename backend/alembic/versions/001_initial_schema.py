revision: str = "001"
down_revision = None
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table("conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("message_count", sa.Integer(), server_default="0"),
        sa.Column("total_tokens", sa.Integer(), server_default="0"),
    )
    op.create_table("messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_redacted", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("sequence_num", sa.Integer(), nullable=False),
    )
    op.create_table("inference_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id"), nullable=True),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("request_id", sa.String(100), unique=True, nullable=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_type", sa.String(100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("input_preview", sa.String(300), nullable=True),
        sa.Column("output_preview", sa.String(300), nullable=True),
        sa.Column("is_streaming", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("time_to_first_token_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("raw_metadata", postgresql.JSONB(), nullable=True),
    )
    op.create_index("idx_inference_logs_created_at", "inference_logs", ["created_at"])
    op.create_index("idx_inference_logs_provider", "inference_logs", ["provider"])
    op.create_index("idx_inference_logs_status", "inference_logs", ["status"])
    op.create_index("idx_messages_conversation_id", "messages", ["conversation_id"])

def downgrade():
    op.drop_index("idx_messages_conversation_id", table_name="messages")
    op.drop_index("idx_inference_logs_status", table_name="inference_logs")
    op.drop_index("idx_inference_logs_provider", table_name="inference_logs")
    op.drop_index("idx_inference_logs_created_at", table_name="inference_logs")
    op.drop_table("inference_logs")
    op.drop_table("messages")
    op.drop_table("conversations")
