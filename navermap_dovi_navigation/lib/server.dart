import 'dart:io';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'notification_service.dart';
import 'package:flutter_tts/flutter_tts.dart';

// Text-to-Speech 서비스 초기화
final FlutterTts _flutterTts = FlutterTts();

Future<void> initializeTTS() async {
  await _flutterTts.setLanguage("en-US"); // 언어 설정
  await _flutterTts.setSpeechRate(0.5); // 속도 설정
  await _flutterTts.setPitch(1.0); // 음성 톤 설정
  print('TTS Initialized');
}

Future<void> speakText(String text) async {
  try {
    await _flutterTts.speak(text);
    print('Speaking: $text');
  } catch (e) {
    print('Error in TTS: $e');
  }
}

Future<void> sendDataToServer(String url, Map<String, dynamic> data) async {
  try {
    print('Sending data to server...');
    final uri = Uri.parse(url);
    final response = await http.post(
      uri,
      headers: {
        "Content-Type": "application/json", // JSON 형식으로 전송
      },
      body: jsonEncode(data), // JSON으로 변환
    );

    if (response.statusCode == 200) {
      print('Data sent successfully.');
      print('Response: ${response.body}');

      // 서버 응답 처리
      processResponse(response.body);
    } else {
      print('Failed to send data. Status code: ${response.statusCode}');
    }
  } on http.ClientException catch (e) {
    print('ClientException: Unable to connect to the server. Error: $e');
  } on SocketException catch (e) {
    print('SocketException: Network error. Check your server and network connection. Error: $e');
  } on FormatException catch (e) {
    print('FormatException: Invalid response format. Error: $e');
  } catch (e) {
    print('Unexpected error: $e');
  } finally {
    print('Request completed.');
  }
}

void processResponse(String responseBody) async {
  try {
    // bad_type 매핑: 영어 key → 한국어 번역
    final Map<String, String> badTypeMapping = {
      'reflective_crack': '반사균열',
      'longitudinal_crack': '세로방향 균열',
      'shear_crack': '밀림 균열',
      'rutting': '밀림 균열',
      'corrugation_and_shoving': '요철 및 밀림',
      'depression': '함몰',
      'pothole': '포트홀',
      'labeling': '라벨링',
      'stripping': '박리',
      'normal': '정상', //없음
      'edge_crack': '단부 균열',
      'construction_crack': '시공균열',
      'alligator_crack': '거북등 균열',
    };

    List<dynamic> responseData = jsonDecode(responseBody);

    if (responseData.isEmpty) {
      print('No data received');
      return;
    }

    // risk_level 기준으로 내림차순 정렬
    responseData.sort((a, b) => (b['risk_level'] ?? 0.0).compareTo(a['risk_level'] ?? 0.0));

    // 가장 위험도가 높은 항목 선택
    var highestRiskItem = responseData.first;
    final double riskLevel = highestRiskItem['risk_level'] ?? 0.0;

    // bad_type이 숫자로 들어온다면 숫자→문자열 맵핑 필요
    // 일단 숫자를 직접 문자열 맵핑해야 한다면 다음과 같이 처리:
    final Map<int, String> badTypeNumberMapping = {
      0: 'reflective_crack',
      1: 'longitudinal_crack',
      2: 'shear_crack',
      3: 'rutting',
      4: 'corrugation_and_shoving',
      5: 'depression',
      6: 'pothole',
      7: 'labeling',
      8: 'stripping',
      9: 'normal',
      10: 'edge_crack',
      11: 'construction_crack',
      12: 'alligator_crack',
    };

    final int rawBadTypeInt = highestRiskItem['bad_type'] ?? -1;
    final String rawBadTypeStr = badTypeNumberMapping[rawBadTypeInt] ?? 'unknown';
    final String badType = badTypeMapping[rawBadTypeStr] ?? 'Unknown Type';

    String notificationTitle;
    String notificationBody;

    if (riskLevel > 0.9) {
      notificationTitle = '고위험도 장애물 알림';
      notificationBody = '현재 경로에서 $badType이 발견되었습니다.감속해주세요.';
      await NotificationService.showHtmlBigTextNotification(notificationTitle, notificationBody);
      await speakText('현재 경로에서 $badType이 발견되었습니다 감속해주세요');
    }
    else if (riskLevel > 0.3) {
      notificationTitle = '저위험도 장애물 알림';
      notificationBody = '현재 경로에서 $badType이 발견되었습니다. 유의해주세요.';
      await NotificationService.showHtmlBigTextNotification(notificationTitle, notificationBody);
      await speakText('현재 경로에서 $badType이 발견되었습니다 유의해주세요');
    }

  } on FormatException catch (e) {
    print('Error decoding JSON: $e');
  } catch (e) {
    print('Unexpected error while processing response: $e');
  }
}

