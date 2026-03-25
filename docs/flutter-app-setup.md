# LunaVis Flutter App Setup

This guide sets up a Flutter mobile app that uses your existing Django API.

## 1) Install Flutter (Windows)

1. Download Flutter SDK: https://docs.flutter.dev/get-started/install/windows/mobile
2. Add Flutter to PATH.
3. Verify:

```powershell
flutter --version
flutter doctor
```

Fix anything Flutter Doctor reports before continuing.

## 2) Create the Flutter app

From the repository root:

```powershell
flutter create luna_vis_mobile
cd luna_vis_mobile
```

## 3) Add dependencies

```powershell
flutter pub add dio flutter_secure_storage intl
```

Optional packages for later:

```powershell
flutter pub add geolocator timezone
```

## 4) Use the correct backend URL

Your Django routes are:
- /api/v1/daily/
- /api/v1/visibility/
- /api/v1/visibility-window/
- /api/v1/location-meta/
- /api/v1/register/
- /api/v1/me/
- /api/token/
- /api/token/refresh/

Use these base URLs by platform during development:
- Android emulator: http://10.0.2.2:8000
- iOS simulator: http://127.0.0.1:8000
- Physical phone: http://<YOUR_PC_LOCAL_IP>:8000

Run Django so devices can reach it:

```powershell
python manage.py runserver 0.0.0.0:8000
```

## 5) Recommended Flutter folder structure

Inside luna_vis_mobile/lib:

- main.dart
- app.dart
- core/
  - config.dart
  - auth_storage.dart
  - api_client.dart
- features/
  - auth/
    - auth_service.dart
    - login_page.dart
    - register_page.dart
  - daily/
    - daily_service.dart
    - daily_page.dart
  - visibility/
    - visibility_service.dart
    - visibility_page.dart

## 6) Core config (lib/core/config.dart)

```dart
class AppConfig {
  // Override at run-time with --dart-define=API_BASE_URL=...
  static const apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );
}
```

## 7) Token storage (lib/core/auth_storage.dart)

```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthStorage {
  static const _storage = FlutterSecureStorage();
  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';

  Future<void> saveTokens({required String access, required String refresh}) async {
    await _storage.write(key: _accessKey, value: access);
    await _storage.write(key: _refreshKey, value: refresh);
  }

  Future<String?> getAccessToken() => _storage.read(key: _accessKey);
  Future<String?> getRefreshToken() => _storage.read(key: _refreshKey);

  Future<void> clear() async {
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
  }
}
```

## 8) API client with JWT refresh (lib/core/api_client.dart)

```dart
import 'package:dio/dio.dart';
import 'config.dart';
import 'auth_storage.dart';

class ApiClient {
  final Dio dio;
  final AuthStorage storage;

  ApiClient(this.storage)
      : dio = Dio(BaseOptions(
          baseUrl: AppConfig.apiBaseUrl,
          connectTimeout: const Duration(seconds: 20),
          receiveTimeout: const Duration(seconds: 20),
          headers: {'Accept': 'application/json'},
        )) {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await storage.getAccessToken();
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (err, handler) async {
          final isUnauthorized = err.response?.statusCode == 401;
          final retried = err.requestOptions.extra['retried'] == true;

          if (!isUnauthorized || retried) {
            return handler.next(err);
          }

          try {
            final refresh = await storage.getRefreshToken();
            if (refresh == null || refresh.isEmpty) {
              return handler.next(err);
            }

            final refreshResponse = await dio.post(
              '/api/token/refresh/',
              data: {'refresh': refresh},
              options: Options(headers: {'Authorization': null}),
            );

            final newAccess = refreshResponse.data['access'] as String;
            await storage.saveTokens(access: newAccess, refresh: refresh);

            final request = err.requestOptions;
            request.extra['retried'] = true;
            request.headers['Authorization'] = 'Bearer $newAccess';

            final replay = await dio.fetch(request);
            return handler.resolve(replay);
          } catch (_) {
            await storage.clear();
            return handler.next(err);
          }
        },
      ),
    );
  }
}
```

## 9) Auth service (lib/features/auth/auth_service.dart)

```dart
import 'package:dio/dio.dart';
import '../../core/api_client.dart';
import '../../core/auth_storage.dart';

class AuthService {
  final ApiClient api;
  final AuthStorage storage;

  AuthService(this.api, this.storage);

  Future<void> login({required String username, required String password}) async {
    final response = await api.dio.post('/api/token/', data: {
      'username': username,
      'password': password,
    });

    await storage.saveTokens(
      access: response.data['access'] as String,
      refresh: response.data['refresh'] as String,
    );
  }

  Future<void> register({
    required String username,
    required String email,
    required String password,
    required String passwordConfirm,
  }) async {
    await api.dio.post('/api/v1/register/', data: {
      'username': username,
      'email': email,
      'password': password,
      'password_confirm': passwordConfirm,
    });
  }

  Future<Map<String, dynamic>> me() async {
    final response = await api.dio.get('/api/v1/me/');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<void> logout() => storage.clear();
}
```

## 10) Daily service (lib/features/daily/daily_service.dart)

```dart
import '../../core/api_client.dart';

class DailyService {
  final ApiClient api;
  DailyService(this.api);

  Future<Map<String, dynamic>> fetchDaily({
    required double lat,
    required double lon,
    required String date,
    required String tz,
    int elevationM = 0,
  }) async {
    final response = await api.dio.get('/api/v1/daily/', queryParameters: {
      'lat': lat,
      'lon': lon,
      'date': date,
      'tz': tz,
      'elevation_m': elevationM,
    });

    return Map<String, dynamic>.from(response.data as Map);
  }
}
```

## 11) Visibility service (lib/features/visibility/visibility_service.dart)

```dart
import '../../core/api_client.dart';

class VisibilityService {
  final ApiClient api;
  VisibilityService(this.api);

  Future<Map<String, dynamic>> fetchVisibility({
    required double lat,
    required double lon,
    required String date,
    required String tz,
    int elevationM = 0,
  }) async {
    final response = await api.dio.get('/api/v1/visibility/', queryParameters: {
      'lat': lat,
      'lon': lon,
      'date': date,
      'tz': tz,
      'elevation_m': elevationM,
    });
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> fetchVisibilityWindow({
    required double lat,
    required double lon,
    required String startDate,
    required String tz,
    int elevationM = 0,
    int nights = 5,
  }) async {
    final response = await api.dio.get('/api/v1/visibility-window/', queryParameters: {
      'lat': lat,
      'lon': lon,
      'start_date': startDate,
      'tz': tz,
      'elevation_m': elevationM,
      'nights': nights,
    });
    return Map<String, dynamic>.from(response.data as Map);
  }
}
```

## 12) Run with platform-specific backend URL

Android emulator:

```powershell
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

iOS simulator:

```powershell
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

Physical device:

```powershell
flutter run --dart-define=API_BASE_URL=http://<YOUR_PC_LOCAL_IP>:8000
```

## 13) Suggested migration order

1. Implement auth (login/register/me).
2. Port Daily Moon Data screen.
3. Port Visibility and Visibility Window screen.
4. Add favourites and observations.
5. Add verify-email and reset-password flows.

## Notes

- Your backend already exposes OpenAPI docs at /api/docs/ and schema at /api/schema/.
- If Android blocks non-HTTPS traffic in release mode, add a network security config for cleartext dev traffic, or use HTTPS/tunnel for development.
