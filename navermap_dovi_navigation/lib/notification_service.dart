import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  static final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
  FlutterLocalNotificationsPlugin();

  static const AndroidNotificationChannel _channel = AndroidNotificationChannel(
    'channel_id',
    'channel_name',
    importance: Importance.high,
  );

  static Future<void> initializeNotifications() async {
    const AndroidInitializationSettings initAndroid =
    AndroidInitializationSettings('@mipmap/ic_launcher');

    final InitializationSettings initSettings =
    InitializationSettings(android: initAndroid);

    await flutterLocalNotificationsPlugin.initialize(initSettings);

    await flutterLocalNotificationsPlugin
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(_channel);
  }

  static Future<void> showHtmlBigTextNotification(String title, String body) async {
    final BigTextStyleInformation bigTextStyleInformation = BigTextStyleInformation(
      body,
      htmlFormatBigText: true,          // bigText 내용 HTML 처리
      contentTitle: title,
      htmlFormatContentTitle: true,     // contentTitle HTML 처리
    );

    final AndroidNotificationDetails androidDetails = AndroidNotificationDetails(
      'channel_id',
      'channel_name',
      importance: Importance.high,
      priority: Priority.high,
      styleInformation: bigTextStyleInformation,
    );

    final NotificationDetails platformDetails = NotificationDetails(android: androidDetails);

    await flutterLocalNotificationsPlugin.show(
      12345,
      title,
      body,
      platformDetails,
      payload: 'item_x',
    );
  }
}
