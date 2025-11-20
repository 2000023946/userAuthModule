System Structure:
set up user login/auth, with jwt token that has 
lots of server sharing one regional DB and has a
cache to reduce the DB hits for token refresh
allowing for new refresh tokens every time access
is made new. Uses amazon aurora DB with the read and write 
copies. 

Functional Requirements:
1. User auth
    * Register a new user with username and password
    * Login with credentials
    * Logout user and invalidate access/refresh tokens
2. Token Management
    * Issue JWT access token upon successful login
    * issue and rorate refresh token each access is refreshed
    * Validate tokens on API requests 
    * Support token revocation
3. Cache Management
    * Store tokens in cache for quick validation
    * update cache asynchronouly when tokens are rotated
    * clean up expired tokens automatically 
4. Mutli-Region Support
    * route user requests to nearest regional server/DB 
    * replicate refresh tokens updates asynchronouly to nearby regions
    * handle cross-regions refreshes gracefully (via replication or home-region)
5. Database Operations
    * Maintain a regional DB per region as a source of truth
    * support writes/updates for token rotations
    * keep DB in sycn with cache (asynchronouly if needed)
6. Loggin & Monitoring
    * Log login attemps, token refresh events, cache hits/misses
    * provide metrics on token usage, DB load, and cache efficiency.

Non-Functional Requirements:
1. Performance
    * Access token validation should be stateless and fast, without DB hits
    * refresh token validation should have low latency via cache. with DB fallback
2. Scalability
    * System must handle millions of users per region
    * Reginoal DB and servers should scale horizontally as user load grows
3. Availability
    * Each region should be highly available, serving local users even if another region fails
    * system should tolerate networks partitions (CAP trade-offs handled by replication)
4. Consistency 
    * Access tokens are stateless --> no cosistency needed
    * Refresh tokens replicated asynchronouly --> eventual consistency accpeted 
5. Security
    * JWTs signed and verified to prevent tampering 
    * Refresh tokens roated to reduce risk if comprised
    * Sensitive user info stored securely (hashed or encrypted)
6. Maintainability
    * Modular architecture to allow adding new regions or databases
    * Celery workers manage asynchronouly tasks without blocking main API

Use Cases:
1. User Login
Actors: User, Auth Server, Regional DB, Cache
Flow:
    * User sends credentials to nearest server
    * Server validates against cahce/DB
    * if valid, server issues access token + refresh token
    * Refresh, token stored in DB and cached
2. Access API with JWT
Actors: User, API Server
Flow:
    * User sends request with access token
    * API server verifies token locally (no DB hit)
    * if valid -> serve request
    * if expired -> prompt refresh Flow
3. Refresh Access Token
Actors: User, Auth Server, Cache, Regional DB, Celery Worker
Flow: 
    * User sends refresh token to server
    * Server checks cache; if missing, checks DB
    * If valid -> issue new access token and rorate refresh token
    * Update cahce and replicate token to nearby regions asynchronouly
4. Logout / Token revocation
Actors: User, Auth Server, DB, Cache
Flow:
    * User logs outs
    * Server invalidates refresh token in DB and cache
    * propagate invalidation to replicated regions asynchronouly
5. Cross-Region User
Actors: User travelling, Regional DBs, Replication System
Flow: 
    * User connects from new region
    * Server checks local DB cache:
        * if refresh exists -> validates locally
        * if not -> proxy to user's home region or use replicated token
        * New access token issued locally

Recommended Order Recap

DB models / schema

Write tests for core behaviors

Implement core functionality (DB-only login, token handling)

Add cache layer (Redis) for token validation

Add Celery for async cleanup / replication

Add multi-region / sharding

Add logging, metrics, and monitoring

------- TESTING ----------

Name                                     Stmts   Miss  Cover
------------------------------------------------------------
UserAuthModule/__init__.py                   0      0   100%
UserAuthModule/logger.py                    43     12    72%
UserAuthModule/settings.py                  44      0   100%
UserAuthModule/test.py                       0      0   100%
UserAuthModule/trace.py                     41      5    88%
UserAuthModule/urls.py                       3      0   100%
api/__init__.py                              0      0   100%
api/admin.py                                 0      0   100%
api/apps.py                                  4      0   100%
api/builder.py                             155     16    90%
api/cache.py                                17      1    94%
api/db_routers.py                            9      0   100%
api/loggers.py                              69      8    88%
api/metrics.py                             167     25    85%
api/middleware.py                           24      0   100%
api/migrations/0001_initial.py               6      0   100%
api/migrations/__init__.py                   0      0   100%
api/models.py                               37      9    76%
api/o_auth_start.py                         21      1    95%
api/serializer.py                           17      9    47%
api/services.py                            123      9    93%
api/states.py                              217     10    95%
api/tests/__init__.py                        0      0   100%
api/tests/test_builder.py                  155      5    97%
api/tests/test_logger.py                    32      1    97%
api/tests/test_login.py                     22      0   100%
api/tests/test_logout.py                    19      0   100%
api/tests/test_metrics.py                   27      1    96%
api/tests/test_oauth.py                     22      0   100%
api/tests/test_password_reset.py            26      0   100%
api/tests/test_register.py                  73      0   100%
api/tests/test_services.py                 113      4    96%
api/tests/test_states.py                   128      7    95%
api/tests/test_third_party_login.py         35      0   100%
api/tests/test_third_party_register.py      32      0   100%
api/tests/test_validaters.py               165      0   100%
api/tests/test_validation.py                25      0   100%
api/tests/test_views.py                     90      0   100%
api/tracers.py                               9      0   100%
api/urls.py                                  7      1    86%
api/utils.py                                40      5    88%
api/validators.py                          151     12    92%
api/views.py                               138     11    92%
manage.py                                   11      2    82%
------------------------------------------------------------
TOTAL                                     2317    154    93%
