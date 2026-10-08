# 同步协议

本文档定义学校端与云端之间的数据同步协议。

## 传输层

- HTTPS / mTLS
- 请求签名 HMAC-SHA256
- 每个学校持有独立的 `school_id` + `api_key`

## 同步批次 (Sync Batch)

```
Batch:
  id: UUID
  school_id: str
  direction: up | down
  entities: EntityChange[]
  checksum: sha256
  created_at: timestamp

EntityChange:
  entity_type: str (e.g. "student")
  record_id: str
  op: INSERT | UPDATE | DELETE
  payload: JSON
  version: monotonic counter (per record)
  changed_at: timestamp
  changed_by: user_id
```

## 流程

1. School Server 每隔 N 秒 / 手动触发 Pull 指令
2. Cloud 返回本学校上次 checkpoint 之后的下行批次
3. School 应用下行变更 → 上报 ACK + checkpoint
4. School 收集本地变更，打包上行批次发送
5. Cloud 接收并处理 → 返回结果 + 新 checkpoint
