# API 总览

EduKit 后端采用 RESTful API 设计，基于 Django REST Framework。

## 基础信息

- Base URL (本地): `http://<school-server>/api/v1/`
- Base URL (云端): `https://cloud.edukit.example.com/api/v1/`
- 认证方式：JWT (Bearer Token)
- 数据格式：JSON
- 字符编码：UTF-8

## 版本策略

URL 中显式包含版本号 `/api/v1/`，不兼容变更通过升级版本号发布。

## 通用响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": { },
  "meta": { "page": 1, "page_size": 20, "total": 100 }
}
```

## 主要资源分组

- `/api/v1/auth/` - 认证、注册、Token 刷新
- `/api/v1/users/` - 用户、角色、权限
- `/api/v1/organization/` - 学校、班级、组织架构
- `/api/v1/teaching/` - 课程、课表、教材、作业
- `/api/v1/exam/` - 考试、成绩、分析
- `/api/v1/sync/` - 云边同步相关端点
