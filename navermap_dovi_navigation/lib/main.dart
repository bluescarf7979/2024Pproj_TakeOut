import 'package:flutter/material.dart';
import 'package:flutter_naver_map/flutter_naver_map.dart'; // NaverMapSdk 사용을 위해 import
import 'map_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // NaverMap SDK 초기화
  await NaverMapSdk.instance.initialize(
    clientId: 'crcyk29d51', // 네이버 클라우드 플랫폼에서 발급받은 Client ID
    onAuthFailed: (status) {
      print('네이버 지도 인증 실패: $status');
    },
  );

  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Naver Map Example',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: MapScreen(),
    );
  }
}
