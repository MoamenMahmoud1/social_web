# Social Web

A backend-focused social image bookmarking application built with Django.

Users can authenticate, maintain profiles, follow other users, bookmark images from external websites, like images, browse an activity stream, and explore image rankings.

The project focuses on backend engineering concerns such as secure remote image ingestion, SSRF mitigation, transactional counters, Redis-backed ranking, cursor pagination, query optimization, data integrity, and production deployment.

---

## Highlights

### Backend

* Django authentication and Google OAuth2
* User profiles and follow relationships
* Generic activity stream
* Secure remote image downloading
* SSRF protection
* Image validation and sanitization
* Transactional like/unlike operations
* Denormalized like counters
* Redis-backed image ranking
* Per-user view deduplication
* Graceful Redis failure handling
* Signed keyset cursor pagination
* Query optimization with `select_related`, `Exists`, `Count`, and `only`
* Database constraints and indexes
* PostgreSQL production database
* Gunicorn + Nginx production stack
* Docker Compose
* Focused backend tests

### Frontend

* Responsive Django templates
* Light and dark themes
* Reusable template components
* AJAX like/unlike
* AJAX follow/unfollow
* Infinite image feed
* Responsive navigation
* External CSS and JavaScript

---

## Architecture

```text
Client
  |
  v
Nginx
  |
  v
Gunicorn
  |
  v
Django
  |
  +---------------------+
  |                     |
  v                     v
PostgreSQL             Redis
  |                     |
  |                     +-- image ranking
  |                     +-- view deduplication
  |
  +-- users
  +-- profiles
  +-- images
  +-- likes
  +-- follows
  +-- activities
```

Redis is used for transient and ranking-oriented data.

PostgreSQL remains the source of truth for persistent application state.

---

## Main Applications

```text
social_web/
|
+-- account/
|   +-- authentication
|   +-- profiles
|   +-- users
|   +-- follow system
|   +-- dashboard
|
+-- action/
|   +-- activity stream
|   +-- generic targets
|   +-- duplicate suppression
|
+-- images/
|   +-- image bookmarking
|   +-- secure image ingestion
|   +-- likes
|   +-- cursor pagination
|   +-- Redis ranking
|   +-- tests
|
+-- bookmarks/
    +-- settings
    +-- middleware
    +-- root URLs
    +-- WSGI / ASGI
```

---

# Backend Design

## Secure Image Ingestion

Remote image URLs are treated as untrusted input.

The application does not directly download and store arbitrary user-provided URLs.

Instead, images pass through a validation pipeline:

```text
External URL
    |
    v
URL parsing
    |
    v
Scheme / port validation
    |
    v
DNS resolution
    |
    v
IP validation
    |
    v
SSRF protection
    |
    v
HTTP request
    |
    v
Redirect validation
    |
    v
Size + MIME checks
    |
    v
Pillow verification
    |
    v
Pixel / decompression checks
    |
    v
Image re-encoding
    |
    v
Sanitized stored image
```

Important protections include:

* only HTTP and HTTPS URLs are accepted
* embedded URL credentials are rejected
* unsafe or private network destinations are rejected
* redirects are validated individually
* remote file size is bounded
* HTTP Content-Type is not trusted alone
* Pillow verifies the decoded image
* supported image formats are restricted
* decompression-bomb protection is applied
* images are re-encoded before storage

Re-encoding prevents the original untrusted byte stream from being stored directly and removes unnecessary metadata.

---

## Image Likes

Likes use a ManyToMany relationship as the source of truth.

For efficient reads, each image also stores a denormalized `total_likes` counter.

```text
ManyToMany likes
      |
      | source of truth
      v
Image.total_likes
      |
      | optimized read value
      v
Image feeds / detail pages
```

Like and unlike operations run inside database transactions.

Database-side `F()` expressions are used for counter updates to reduce race-condition risks.

Repeated requests are handled safely so duplicate likes do not repeatedly increment the counter.

---

## Redis Ranking

Image views are ranked using a Redis sorted set.

```text
Redis Sorted Set

image_id       score
--------------------
42              151
18               93
7                64
```

A view increments the image score.

To reduce ranking manipulation from repeated reloads, each user/image pair receives a temporary Redis key.

```text
images:view:<image_id>:user:<user_id>
```

The key expires after the configured window, so repeated visits during that period do not continuously increase the ranking.

If Redis becomes unavailable, ranking functionality degrades gracefully instead of taking down the core image page.

---

## Cursor Pagination

The image feed uses keyset pagination instead of large SQL offsets.

Traditional pagination:

```text
LIMIT 10 OFFSET 0
LIMIT 10 OFFSET 10
LIMIT 10 OFFSET 10000
```

Keyset pagination instead continues from the last item:

```text
ORDER BY created DESC, id DESC

        |
        v

last item from previous page
        |
        v

next result set
```

The cursor contains the ordering boundary and is signed using Django's signing system.

This gives the feed:

* stable ordering
* efficient database access
* no increasingly large OFFSET
* natural infinite-scroll support
* tamper-resistant cursor values

---

## Social Graph

Users can follow and unfollow other users.

The relationship is represented explicitly through the `Contact` model.

```text
User A
   |
   | follows
   v
User B
```

Follow operations validate:

* target user
* requested action
* self-follow attempts
* existing relationships

The update runs transactionally and returns the resulting follower count for the asynchronous UI.

---

## Activity Stream

The activity system records events such as:

```text
user bookmarked image
user liked image
user followed user
```

Django ContentTypes allow an activity to reference different target model types.

```text
Action
 |
 +-- user
 +-- verb
 |
 +-- generic target
        |
        +-- Image
        +-- User
        +-- other supported objects
```

Near-duplicate actions are suppressed within a short time window to avoid flooding the activity feed.

---

# Database Performance

Several views deliberately reduce unnecessary database work.

Techniques include:

```text
select_related()
prefetch_related()
Exists()
OuterRef()
Count()
only()
database indexes
denormalized counters
```

For example, checking whether the current user liked an image uses an `Exists()` subquery rather than loading every liking user.

```text
Image
 |
 +-- owner/profile
 |
 +-- EXISTS(current user like?)
 |
 +-- total_likes
```

Profile pages similarly annotate follower counts and follow status instead of issuing repeated queries from templates.

---

# Security

Security is handled as several independent layers:

```text
Input validation
      |
      v
Authentication
      |
      v
Authorization
      |
      v
Database constraints
      |
      v
Network validation
      |
      v
Image sanitization
      |
      v
Production proxy settings
```

Important protections include:

* Django CSRF protection
* authenticated mutation endpoints
* POST-only state changes
* self-follow prevention
* database constraints
* signed pagination cursors
* SSRF protection
* remote download limits
* MIME and image verification
* image re-encoding
* secure production cookies
* environment-based secrets
* restricted admin access

---

# Authentication

The application supports:

```text
Django sessions
      |
      +-- username/password
      |
      +-- email authentication
      |
      +-- Google OAuth2
```

User profiles are created automatically where required so application users have an associated profile.

---

# Production Stack

```text
Browser
   |
   v
Nginx :80/443
   |
   v
Gunicorn :8000
   |
   v
Django
   |
   +----------+
   |          |
   v          v
PostgreSQL   Redis
```

Responsibilities:

```text
Nginx
+-- public HTTP entry point
+-- reverse proxy
+-- static files
+-- media files

Gunicorn
+-- WSGI application server
+-- Django worker processes

PostgreSQL
+-- persistent relational data

Redis
+-- ranking
+-- temporary view deduplication
```

Celery is intentionally not part of the current architecture because the project currently has no background workload that justifies a dedicated task queue.

---

# Tech Stack

## Backend

```text
Python
Django
PostgreSQL
Redis
Gunicorn
Nginx
```

## Authentication

```text
Django Authentication
social-auth-app-django
Google OAuth2
```

## Images

```text
Pillow
easy-thumbnails
Requests
```

## Frontend

```text
Django Templates
Bootstrap
HTML
CSS
JavaScript
```

## Infrastructure

```text
Docker
Docker Compose
```

---

# Running With Docker

Create a local `.env` file containing the required configuration.

Example:

```env
SECRET_KEY=replace-me

ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=social_web
POSTGRES_USER=social_web
POSTGRES_PASSWORD=replace-me

GOOGLE_OAUTH2_KEY=replace-me
GOOGLE_OAUTH2_SECRET=replace-me
```

Never commit the real `.env` file.

Build:

```bash
docker compose build
```

Start:

```bash
docker compose up -d
```

Check services:

```bash
docker compose ps
```

Create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

Run migrations:

```bash
docker compose exec web python manage.py migrate
```

Run Django checks:

```bash
docker compose exec web python manage.py check
```

Application logs:

```bash
docker compose logs -f web
```

Nginx logs:

```bash
docker compose logs -f nginx
```

For the local Docker configuration, access the application through Nginx:

```text
http://127.0.0.1/
```

---

# Tests

The project contains focused backend tests, including Redis ranking and secure image processing behavior.

Run all tests:

```bash
python manage.py test
```

Or inside Docker:

```bash
docker compose exec web python manage.py test
```

Ranking tests:

```bash
docker compose exec web python manage.py test images.tests.test_ranking -v 2
```

---

# Engineering Decisions

## Why PostgreSQL?

The core application domain is relational:

```text
users
profiles
images
likes
followers
activities
```

These benefit from transactions, constraints, indexes, foreign keys, and relational queries.

## Why Redis?

Ranking and temporary deduplication are naturally represented using Redis sorted sets and TTL-based keys.

Redis does not replace PostgreSQL as the application's durable source of truth.

## Why store `total_likes`?

The ManyToMany relation remains authoritative, while `total_likes` provides a cheap value for frequently rendered image feeds and detail pages.

The tradeoff is a slightly more complicated write path in exchange for a cheaper read path.

## Why keyset pagination?

It avoids increasingly expensive database offsets and maps naturally to an infinite-scroll feed.

## Why re-encode remote images?

The remote image source is untrusted.

Re-encoding stores a new image generated from decoded pixel data instead of persisting arbitrary downloaded bytes directly.

---

# Project Origin

This project started from the Social Website project in **Django 5 By Example** by Antonio Mele, published by Packt.

The original source code is licensed under the MIT License.

This repository contains substantial modifications and additional work, including:

* backend refactoring
* security hardening
* SSRF-safe image ingestion
* image sanitization
* Redis ranking
* view deduplication
* cursor pagination
* transactional like handling
* database optimizations
* activity-stream improvements
* UI redesign
* Docker deployment work
* Gunicorn and Nginx integration
* additional tests

The purpose of this repository is to demonstrate how a learning project can be evolved into a more production-oriented Django application.

---

# License

This project is distributed under the MIT License.

Original project code:

```text
Copyright (c) 2024 Packt
```

Additional modifications in this repository are also distributed under the MIT License.

See `LICENSE` for the complete license text.
