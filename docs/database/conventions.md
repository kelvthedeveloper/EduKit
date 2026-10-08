# 数据库开发约定

## 命名规范

- 表名：小写 + 下划线，使用复数形式，例如 `student_profiles`
- 字段名：小写 + 下划线，例如 `created_at`
- 索引：`idx_<table>_<column(s)>`
- 外键：`fk_<table>_<ref_table>_<column>`

## 通用字段约定

所有业务表必须包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGSERIAL / UUID | 主键 |
| `created_at` | TIMESTAMPTZ | 创建时间 |
| `updated_at` | TIMESTAMPTZ | 更新时间 |
| `created_by` | FK | 创建人 |
| `is_deleted` | BOOLEAN | 软删除标记 |

## 迁移规范

- 每个迁移文件只做一件事
- 禁止破坏性 ALTER (先加新字段，数据迁移后再删旧字段)
- 大数据量表的 DDL 必须在低峰期执行或使用在线迁移工具

## 多租户数据隔离

- 所有业务表增加 `school_id` 字段
- ORM 层强制自动过滤当前学校
