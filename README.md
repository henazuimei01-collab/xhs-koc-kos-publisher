# 小红书 KOC / KOS 批量定时发布

给员工在各自电脑上使用的 Codex 插件。内容和图片保存在员工本机，通过同一份 Excel 模板批量安排不同账号、不同时间的笔记。

## 安装

在 Codex 终端依次运行：

```bash
codex plugin marketplace add henazuimei01-collab/xhs-koc-kos-publisher
codex plugin add xhs-koc-kos-publisher@xhs-tools
```

安装后新建一个 Codex 对话，发送：

> 使用 pgy-submit-kos-note，把批量发布模板复制到我的工作目录。

填写模板后，把 Excel 和图片放在自己的电脑上，再发送：

> 使用 pgy-submit-kos-note，预检并执行这份发布任务。发布前先让我确认。

## 两种发布方式

- KOC：必须填写唯一的蒲公英订单号，从蒲公英订单进入发布。
- KOS：蒲公英订单号留空，直接在小红书创作服务平台发布，禁止绑定商单。

每一行是一篇笔记，可分别填写账号、图片位置和精确到分钟的定时时间。
