import 'dart:async';
import 'dart:io';
import 'dart:math' show cos, sqrt, asin;
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:geofencing_api/geofencing_api.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:geolocator/geolocator.dart' as geo;
import 'package:flutter/services.dart';

import 'package:flutter_naver_map/flutter_naver_map.dart';
import 'server.dart';

const String SERVER_URL = 'http://123.111.161.224:9091/api/road_info/navi/';
const MethodChannel _ttsChannel = MethodChannel('my_tts_channel');
// 변경: 네이버 지도 앱 호출용 MethodChannel 추가
const MethodChannel _mapChannel = MethodChannel('com.example.app/naver_map');

Future<void> startTTSService() async {
  await _ttsChannel.invokeMethod('startTTSService');
}

Future<void> speakText(String text) async {
  await _ttsChannel.invokeMethod('speakText', {"text": text});
}

class NavigationScreen extends StatelessWidget {
  final double lat;
  final double lng;
  const NavigationScreen({required this.lat, required this.lng, Key? key})
      : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('내비게이션 화면'),
      ),
      body: Center(
        child: Text('목적지: $lat, $lng'),
      ),
    );
  }
}

class MapScreen extends StatefulWidget {
  @override
  _MapScreenState createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  late NaverMapController _mapController;
  NLatLng? _currentLocation;
  NLatLng? _destinationLocation;
  NLatLng? _originLocation;

  // 식별용 변수들
  NMarker? _currentMarker;
  NMarker? _destinationMarker;
  NPolylineOverlay? _routePolyline;

  final List<NMarker> _markers = [];
  final List<NPolylineOverlay> _polylines = [];

  final String _clientId = 'crcyk29d51';
  final String _clientSecret = '7hQJgmhSBgHNai3Y8EwrNhArseOJBufmUyDcHeXq';

  final TextEditingController _searchController = TextEditingController();

  String? _distance;
  String? _duration;
  bool _originNotificationSent = false;
  bool _destinationNotificationSent = false;
  double geofenceRadius = 50.0;
  bool _geofencingStarted = false;

  FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
  FlutterLocalNotificationsPlugin();

  static const AndroidNotificationChannel _channel = AndroidNotificationChannel(
    'channel_id',
    'channel_name',
    importance: Importance.high,
  );

  StreamSubscription<geo.Position>? _positionStreamSubscription;

  @override
  void initState() {
    super.initState();
    _initLocalNotifications();
    _initializeLocation();
    _requestNotificationPermission();
  }

  @override
  void dispose() {
    _positionStreamSubscription?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _requestNotificationPermission() async {
    if (Platform.isAndroid) {
      var status = await Permission.notification.status;
      if (status.isDenied || status.isPermanentlyDenied) {
        await Permission.notification.request();
      }
    }
  }

  Future<void> _initLocalNotifications() async {
    const AndroidInitializationSettings initAndroid =
    AndroidInitializationSettings('@mipmap/ic_launcher');

    final InitializationSettings initSettings =
    InitializationSettings(android: initAndroid);

    await flutterLocalNotificationsPlugin.initialize(initSettings);

    await flutterLocalNotificationsPlugin
        .resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(_channel);
  }

  Future<void> _initializeLocation() async {
    bool serviceEnabled = await geo.Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('위치 서비스를 활성화해주세요.')),
      );
      return;
    }

    geo.LocationPermission permission = await geo.Geolocator.checkPermission();
    if (permission == geo.LocationPermission.denied) {
      permission = await geo.Geolocator.requestPermission();
      if (permission == geo.LocationPermission.denied) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('위치 권한이 필요합니다.')),
        );
        return;
      }
    }

    if (permission == geo.LocationPermission.deniedForever) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('위치 권한이 영구적으로 거부되었습니다. 설정에서 권한을 허용해주세요.')),
      );
      return;
    }

    geo.Position position =
    await geo.Geolocator.getCurrentPosition(desiredAccuracy: geo.LocationAccuracy.high);
    _currentLocation = NLatLng(position.latitude, position.longitude);
    _originLocation = _currentLocation;

    // 현재 위치 마커 설정
    _setCurrentMarker(_currentLocation!);

    setState(() {});

    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (_currentLocation != null && _mapController != null) {
        await _mapController.updateCamera(
          NCameraUpdate.fromCameraPosition(
            NCameraPosition(target: _currentLocation!, zoom: 16),
          ),
        );
      }
    });

    _positionStreamSubscription = geo.Geolocator.getPositionStream(
      locationSettings: const geo.LocationSettings(
        accuracy: geo.LocationAccuracy.high,
        distanceFilter: 10,
      ),
    ).listen((geo.Position currentPosition) async {
      NLatLng newLatLng = NLatLng(currentPosition.latitude, currentPosition.longitude);
      _currentLocation = newLatLng;
      _setCurrentMarker(_currentLocation!);

      if (_destinationLocation != null) {
        _distance = _calculateDistance(_currentLocation!, _destinationLocation!).toStringAsFixed(2) + ' km';
      }

      setState(() {});

      if (_destinationLocation != null) {
        await _createRoute();
      }
    });
  }

  void _setCurrentMarker(NLatLng position) {
    // 기존 마커 제거
    if (_currentMarker != null) {
      _markers.remove(_currentMarker);
    }

    _currentMarker = NMarker(
      id: 'currentMarkerId', // 고유한 id 값 지정
      position: position,
      caption: NOverlayCaption(text: '현재 위치'),
    );
    _markers.add(_currentMarker!);
  }

  void _setDestinationMarker(NLatLng position) {
    // 이전 목적지 마커 제거
    if (_destinationMarker != null) {
      _markers.remove(_destinationMarker);
    }
    _destinationMarker = NMarker(
      id: 'destinationMarkerId', // 고유한 id 값 지정
      position: position,
      caption: NOverlayCaption(text: '목적지'),
    );
    _markers.add(_destinationMarker!);
  }

  Future<void> _searchDestination() async {
    final query = _searchController.text;
    if (query.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('목적지 주소를 입력해주세요.')),
      );
      return;
    }

    final encodedQuery = Uri.encodeQueryComponent(query, encoding: utf8);

    // Naver Geocoding API
    final url = Uri.parse('https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query=$encodedQuery');
    final response = await http.get(url, headers: {
      'X-NCP-APIGW-API-KEY-ID': _clientId,
      'X-NCP-APIGW-API-KEY': _clientSecret,
    });

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      if (data['addresses'].isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('유효한 주소를 입력해주세요.')),
        );
        return;
      }

      final addr = data['addresses'][0];
      final double lat = double.parse(addr['y']);
      final double lng = double.parse(addr['x']);
      final destinationLatLng = NLatLng(lat, lng);

      _destinationLocation = destinationLatLng;
      _setDestinationMarker(destinationLatLng);

      _distance = null;
      _duration = null;
      _destinationNotificationSent = false;
      _originNotificationSent = false;

      await _createRoute();
      await _mapController.updateCamera(
        NCameraUpdate.fromCameraPosition(
          NCameraPosition(target: destinationLatLng, zoom: 15),
        ),
      );

      setState(() {});
    } else {
      throw Exception('Failed to load geocode data');
    }
  }

  Future<void> _createRoute() async {
    if (_currentLocation == null || _destinationLocation == null) return;

    final start = '${_currentLocation!.longitude},${_currentLocation!.latitude}';
    final goal = '${_destinationLocation!.longitude},${_destinationLocation!.latitude}';

    final url = Uri.parse(
        'https://naveropenapi.apigw.ntruss.com/map-direction/v1/driving?start=$start&goal=$goal&option=traoptimal');
    final response = await http.get(url, headers: {
      'X-NCP-APIGW-API-KEY-ID': _clientId,
      'X-NCP-APIGW-API-KEY': _clientSecret,
    });

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      if (data['route'] == null || data['route']['traoptimal'] == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('경로를 찾을 수 없습니다.')),
        );
        return;
      }

      final route = data['route']['traoptimal'][0];
      final summary = route['summary'];
      final distance = summary['distance']; // m단위
      final duration = summary['duration']; // ms단위

      List<NLatLng> coords = [];
      for (var section in route['path']) {
        coords.add(NLatLng(section[1], section[0]));
      }

      _distance = (distance / 1000).toStringAsFixed(2) + ' km';
      final durMin = (duration / 60000).ceil();
      _duration = '${durMin}분';

      // 이전 라인 제거
      if (_routePolyline != null) {
        _polylines.remove(_routePolyline);
      }

      // 일정 거리 간격으로 경로 상의 좌표를 얻음
      List<NLatLng> intervalCoordinates = _getCoordinatesAtIntervals(coords, 100.0);
      List<List<double>> coordList = intervalCoordinates.map((c) => [c.latitude, c.longitude]).toList();

      print(coordList);
      // 상위 10개 포인트만 선택
      List<List<double>> top10Coordinates = coordList.take(10).toList();
      // print('100m 간격 점 개수: ${intervalCoordinates.length}');
      for (var point in top10Coordinates) {
        //print('interval coordinate: ${top10Coordinates}');
        print('interval coordinate: ${point[0]}, ${point[1]}');
      }
      print('top10Coordinates: ${top10Coordinates}');

      // 서버로 좌표 리스트 전송
      sendPolylineData(top10Coordinates);

      _routePolyline = NPolylineOverlay(
        id: 'routePolylineId', // 고유한 id 값 지정
        coords: coords,
        color: Colors.blue,
        width: 5,
      );
      _polylines.add(_routePolyline!);

      // 폴리라인 갱신: 경로 생성 후 다시 오버레이 등록
      if (_mapController != null) {
        await _mapController.addOverlayAll(_polylines.toSet());
      }

      setState(() {});
    } else {
      throw Exception('Directions API 요청 실패');
    }
  }
  void sendPolylineData(List<List<double>> polyline) {
    final data = {
      "polyline": polyline
    };
    sendDataToServer(SERVER_URL, data);
  }
  /// 주어진 경로(route)에 대해 일정 거리(metersInterval) 간격으로 좌표를 추출
  List<NLatLng> _getCoordinatesAtIntervals(List<NLatLng> route, double metersInterval) {
    List<NLatLng> result = [];
    if (route.isEmpty) return result;

    // 첫 시작점 추가
    result.add(route.first);

    double totalDistance = 0.0;
    // 전체 경로 길이 계산
    for (int i = 0; i < route.length - 1; i++) {
      totalDistance += _distanceInMeters(route[i], route[i+1]);
    }

    double targetDistance = metersInterval;
    double traveled = 0.0;

    for (int i = 0; i < route.length - 1; i++) {
      final start = route[i];
      final end = route[i+1];
      double segmentDistance = _distanceInMeters(start, end);

      while (traveled + segmentDistance >= targetDistance) {
        double remaining = targetDistance - traveled;
        double factor = remaining / segmentDistance;
        NLatLng interpolatedPoint = _interpolate(start, end, factor);
        result.add(interpolatedPoint);

        targetDistance += metersInterval;
        if (targetDistance > totalDistance) {
          break;
        }
      }
      traveled += segmentDistance;
      if (targetDistance > totalDistance) {
        break;
      }
    }

    // 마지막 점 추가 (필요시)
    if (result.last != route.last) {
      result.add(route.last);
    }

    return result;
  }

  /// 두 좌표 사이 거리(m) 구하기
  double _distanceInMeters(NLatLng start, NLatLng end) {
    const double p = 0.017453292519943295;

    double a = 0.5 - cos((end.latitude - start.latitude) * p)/2 +
        cos(start.latitude * p)*cos(end.latitude * p) *
            (1 - cos((end.longitude - start.longitude) * p))/2;

    return 12742000 * asin(sqrt(a));
  }

  /// 두 점을 factor 비율(0~1)에 따라 선형보간
  NLatLng _interpolate(NLatLng start, NLatLng end, double factor) {
    double lat = start.latitude + (end.latitude - start.latitude) * factor;
    double lng = start.longitude + (end.longitude - start.longitude) * factor;
    return NLatLng(lat, lng);
  }

  double _calculateDistance(NLatLng start, NLatLng end) {
    var p = 0.017453292519943295;
    var c = cos;
    var a = 0.5 -
        c((end.latitude - start.latitude) * p) / 2 +
        c(start.latitude * p) *
            c(end.latitude * p) *
            (1 - c((end.longitude - start.longitude) * p)) / 2;
    return 12742 * asin(sqrt(a));
  }

  void _onMapTapped(NPoint point, NLatLng position) async {
    // 지도 빈 곳을 탭했을 때의 로직

    _destinationLocation = position;
    _setDestinationMarker(position);

    _distance = null;
    _duration = null;
    _destinationNotificationSent = false;
    _originNotificationSent = false;

    await _createRoute();

    // 카메라 목적지로 이동
    if (_mapController != null) {
      await _mapController.updateCamera(
        NCameraUpdate.fromCameraPosition(
          NCameraPosition(target: position, zoom: 15),
        ),
      );
    }

    setState(() {});
  }

  void _onSymbolTapped(NSymbolInfo symbolInfo) async {
    // 심볼을 탭했을 때의 로직
    // symbolInfo.latLng를 사용해 해당 심볼의 좌표로 목적지를 설정할 수 있음
    final latLng = symbolInfo.position;
    _destinationLocation = latLng;
    _setDestinationMarker(latLng);

    _distance = null;
    _duration = null;
    _destinationNotificationSent = false;
    _originNotificationSent = false;

    await _createRoute();
    if (_mapController != null) {
      await _mapController.updateCamera(
        NCameraUpdate.fromCameraPosition(
          NCameraPosition(target: latLng, zoom: 15),
        ),
      );
    }

    setState(() {});
  }

  Future<void> _goToCurrentLocation() async {
    if (_currentLocation != null) {
      await _mapController.updateCamera(
        NCameraUpdate.fromCameraPosition(
          NCameraPosition(target: _currentLocation!, zoom: 15),
        ),
      );
    }
  }

  Future<bool> _requestLocationPermissionForGeofence() async {
    var status = await Permission.location.request();
    return status.isGranted;
  }

  Future<void> _onGeofenceStatusChanged(
      GeofenceRegion region, GeofenceStatus status, Location location) async {
    if (region.id == 'origin_region' &&
        status == GeofenceStatus.enter &&
        !_originNotificationSent) {
      await _showNotification('출발 준비 완료', '출발지 근처에 있습니다. 이제 출발하세요!');
      _originNotificationSent = true;
      await startTTSService();
      await speakText('출발 준비 완료, 출발지 근처에 있습니다. 이제 출발하세요!');
    }

    if (region.id == 'destination_region' &&
        status == GeofenceStatus.enter &&
        !_destinationNotificationSent) {
      await _showNotification('목적지 인근 도착', '목적지 근처에 도착했습니다. 주의하세요!');
      _destinationNotificationSent = true;
      await speakText('목적지 인근 도착, 목적지 근처에 도착했습니다. 주의하세요!');
    }

    setState(() {});
  }

  void _onGeofenceError(Object error, StackTrace stackTrace) {
    print('Geofence error: $error\n$stackTrace');
  }

  Future<void> _startGeofencing() async {
    if (_geofencingStarted) return;
    if (_originLocation == null || _destinationLocation == null) return;

    final originRegion = GeofenceRegion.circular(
      id: 'origin_region',
      data: {'name': '출발지'},
      center: LatLng(_originLocation!.latitude, _originLocation!.longitude),
      radius: geofenceRadius,
      loiteringDelay: 60 * 1000,
    );

    final destinationRegion = GeofenceRegion.circular(
      id: 'destination_region',
      data: {'name': '목적지'},
      center: LatLng(_destinationLocation!.latitude, _destinationLocation!.longitude),
      radius: geofenceRadius,
      loiteringDelay: 60 * 1000,
    );

    final regions = {originRegion, destinationRegion};

    bool granted = await _requestLocationPermissionForGeofence();
    if (!granted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('지오펜싱을 위해 위치 권한이 필요합니다.')),
      );
      return;
    }

    Geofencing.instance.setup(
      interval: 5 * 1000,
      accuracy: 100,
      statusChangeDelay: 10 * 1000,
      allowsMockLocation: true,
      printsDebugLog: true,
    );

    Geofencing.instance.addGeofenceStatusChangedListener(
            (region, status, location) async {
          await _onGeofenceStatusChanged(region, status, location);
        });
    Geofencing.instance.addGeofenceErrorCallbackListener(_onGeofenceError);

    await Geofencing.instance.start(regions: regions);
    _geofencingStarted = true;
  }

  Future<void> _startNavigation() async {
    if (_destinationLocation == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('목적지를 먼저 설정해주세요.')),
      );
      return;
    }

    await _startGeofencing();

    final lat = _destinationLocation!.latitude;
    final lng = _destinationLocation!.longitude;

    final start_lat = _currentLocation!.latitude;
    final start_lng = _currentLocation!.longitude;


    final startName = Uri.encodeComponent('출발지');
    final destName = Uri.encodeComponent('도착지');

    final uri = Uri.parse(
        'nmap://route/car?slat=$start_lat&slng=$start_lng&sname=$startName&dlat=$lat&dlng=$lng&dname=$destName&appname=com.example.gmap');
    bool launched = false;

    if (await canLaunchUrl(uri)) {
      launched = await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else {
      final webUri =
      Uri.parse('https://map.naver.com/v5/directions/-/$lng,$lat/car');
      if (await canLaunchUrl(webUri)) {
        launched = await launchUrl(webUri, mode: LaunchMode.externalApplication);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('네이버 맵을 실행할 수 없습니다. 앱 설치 또는 브라우저 지원 필요')),
        );
      }
    }

    if (launched) {
      await startTTSService();
      await _showNotification('네비게이션 모드입니다', '목적지 방향으로 안내 중입니다.');
      await speakText('네비게이션 모드입니다, 목적지 방향으로 안내 중입니다.');

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => NavigationScreen(
            lat: _destinationLocation!.latitude,
            lng: _destinationLocation!.longitude,
          ),
        ),
      );
    }
  }

  Future<void> _showNotification(String title, String body) async {
    const AndroidNotificationDetails androidDetails = AndroidNotificationDetails(
      'channel_id',
      'channel_name',
      importance: Importance.high,
      priority: Priority.high,
      playSound: true,
    );

    const NotificationDetails platformDetails =
    NotificationDetails(android: androidDetails);

    await flutterLocalNotificationsPlugin.show(
      0,
      title,
      body,
      platformDetails,
      payload: 'item_x',
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _searchController,
                decoration: InputDecoration(
                  hintText: '목적지 주소 입력...',
                  filled: true,
                  fillColor: Colors.white,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8.0),
                    borderSide: BorderSide.none,
                  ),
                  contentPadding: EdgeInsets.symmetric(horizontal: 10.0),
                ),
                onSubmitted: (value) {
                  _searchDestination();
                },
              ),
            ),
            IconButton(
              icon: Icon(Icons.search, color: Colors.white),
              onPressed: _searchDestination,
            ),
          ],
        ),
        backgroundColor: Colors.blue,
      ),
      body: Stack(
        children: [
          NaverMap(
            onMapReady: (controller) async {
              _mapController = controller;
              if (_markers.isNotEmpty) {
                await _mapController.addOverlayAll(_markers.toSet());
              }
              if (_polylines.isNotEmpty) {
                await _mapController.addOverlayAll(_polylines.toSet());
              }
              // 현재 위치 오버레이 활성화
              final locationOverlay = _mapController.getLocationOverlay();

              locationOverlay.setIsVisible(true);
              locationOverlay.setPosition(_currentLocation ?? NLatLng(37.5665, 126.9780));
              locationOverlay.setAnchor(NPoint(0.5, 0.5));
              // 위치 추적 모드 설정 (Follow 모드로 하면 카메라가 현재 위치 따라감)
              await _mapController.setLocationTrackingMode(NLocationTrackingMode.follow);


            },
            onMapTapped: (point, latLng) {
              _onMapTapped(point, latLng);
            },
            onSymbolTapped: (symbolInfo) {
              // 심볼(POI)을 탭했을 때 호출되는 콜백
              // symbolInfo에는 심볼의 좌표, 이름 등의 정보가 들어있습니다.
              // 이 정보로 목적지 설정, 혹은 심볼에 관련된 상세정보 UI 표시 등을 할 수 있습니다.
              _onSymbolTapped(symbolInfo);
            },
            options: NaverMapViewOptions(
              initialCameraPosition: NCameraPosition(
                target: _currentLocation ?? NLatLng(37.5665, 126.9780),
                zoom: 11.0,
              ),
              //indoorEnable: true,
            ),
          ),
          Positioned(
            top: 40,
            right: 10,
            child: FloatingActionButton(
              onPressed: _goToCurrentLocation,
              child: Icon(Icons.my_location),
              backgroundColor: Colors.blue,
            ),
          ),
          if (_distance != null && _duration != null)
            Positioned(
              bottom: 20,
              left: 10,
              right: 60,
              child: Container(
                padding: EdgeInsets.all(15.0),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.9),
                  borderRadius: BorderRadius.circular(10.0),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black26,
                      blurRadius: 5.0,
                      offset: Offset(0, 2),
                    ),
                  ],
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '거리: $_distance',
                      style: TextStyle(
                        fontSize: 16.0,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      '소요 시간: $_duration',
                      style: TextStyle(
                        fontSize: 16.0,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    IconButton(
                      icon: Icon(Icons.navigation, color: Colors.blue),
                      onPressed: _startNavigation,
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
