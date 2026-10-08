# 认证 (Authentication)

## 认证方式

| 场景 | 方式 |
|------|------|
| Web 登录 (教师/学生) | 账号密码 + JWT Access/Refresh Token |
| 管理后台 | 账号密码 + MFA (TOTP) |
| API 对接 | OAuth 2.0 Client Credentials |
| 云边同步 | mTLS + API Key + HMAC 签名 |
| 微信 / 钉钉 / LTI | OAuth 2.0 第三方登录 |

## Token 生命周期

- Access Token：15 分钟，不可撤销 (黑名单可选)
- Refresh Token：7 天，可撤销，可轮换
- 登录失败：5 次锁定 30 分钟，防止暴力破解

## 密码策略

- 最小长度 8 位
- 必须包含大写、小写、数字、特殊字符中至少 3 种
- 90 天强制更换 (可配置)
- 禁止使用最近 5 次历史密码
