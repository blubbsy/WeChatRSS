# API Reference

WeChatRSS provides a RESTful API built with FastAPI.

## Authentication

Most endpoints require a `session_id` cookie, obtained via the login endpoint.

### Login
`POST /login`
*   **Form Data:** `username`, `password`
*   **Returns:** Redirects to `/` with a `session_id` cookie.

### Logout
`GET /logout`
*   **Returns:** Clears cookie and redirects to login.

## User Management (Admin Only)

### List Users
`GET /users`

### Create User
`POST /users`
*   **Body:** `{"username": "...", "password": "...", "role": "..."}`

### Delete User
`DELETE /users/{user_id}`

## Account Subscriptions

### List Accounts
`GET /accounts`
*   **Returns:** Accounts followed by the current user.

### Add Account
`POST /accounts`
*   **Body:** `{"id": "MP_ID", "name": "DisplayName"}`

## RSS Feeds

### Get Private Feed
`GET /rss/{feed_hash}`
*   **Parameters:** `feed_hash` (unique per user).
*   **Returns:** Application/XML RSS 2.0 feed.

## System Settings (Admin Only)

### Get Settings
`GET /settings`

### Update Settings
`POST /settings`
*   **Body:** `{"settings": {"key": "value"}}`
*   **Note:** Triggers a scraper scheduler restart.
