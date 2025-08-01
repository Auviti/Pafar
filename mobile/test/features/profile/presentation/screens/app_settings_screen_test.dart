import 'package:flutter/material.dart' hide ThemeMode;
import 'package:flutter_test/flutter_test.dart';

import 'package:pafar_mobile/features/profile/presentation/screens/app_settings_screen.dart';

void main() {

  Widget createWidgetUnderTest() {
    return const MaterialApp(
      home: AppSettingsScreen(),
    );
  }

  group('AppSettingsScreen Widget Tests', () {
    testWidgets('should display app bar with correct title', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('App Settings'), findsOneWidget);
      expect(find.byType(AppBar), findsOneWidget);
    });

    testWidgets('should display section headers', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Appearance'), findsOneWidget);
      expect(find.text('Security'), findsOneWidget);
      expect(find.text('Privacy'), findsOneWidget);
      expect(find.text('About'), findsOneWidget);
    });

    testWidgets('should display appearance settings', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Theme'), findsOneWidget);
      expect(find.text('Language'), findsOneWidget);
      expect(find.byType(DropdownButton), findsNWidgets(2)); // Theme and Language dropdowns
    });

    testWidgets('should display security settings', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Biometric Authentication'), findsOneWidget);
      expect(find.text('Auto Lock'), findsOneWidget);
      expect(find.byType(Switch), findsNWidgets(4)); // Biometric, Auto Lock, Location, Crash Reporting
    });

    testWidgets('should display privacy settings', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Location Services'), findsOneWidget);
      expect(find.text('Crash Reporting'), findsOneWidget);
    });

    testWidgets('should display about section', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('App Version'), findsOneWidget);
      expect(find.text('Privacy Policy'), findsOneWidget);
      expect(find.text('Terms of Service'), findsOneWidget);
      expect(find.text('Help & Support'), findsOneWidget);
      expect(find.text('1.0.0 (Build 1)'), findsOneWidget);
    });

    testWidgets('should show auto lock duration when auto lock is enabled', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();
      
      // Enable auto lock by tapping the switch
      final autoLockSwitch = find.widgetWithText(ListTile, 'Auto Lock');
      await tester.tap(autoLockSwitch);
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Auto Lock Duration'), findsOneWidget);
    });

    testWidgets('should show privacy policy dialog when tapped', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();
      
      await tester.tap(find.text('Privacy Policy'));
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Privacy Policy'), findsNWidgets(2)); // One in list, one in dialog
      expect(find.text('This is a placeholder for the privacy policy'), findsOneWidget);
    });

    testWidgets('should show terms of service dialog when tapped', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();
      
      await tester.tap(find.text('Terms of Service'));
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Terms of Service'), findsNWidgets(2)); // One in list, one in dialog
      expect(find.text('This is a placeholder for the terms of service'), findsOneWidget);
    });

    testWidgets('should show help dialog when help & support is tapped', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();
      
      await tester.tap(find.text('Help & Support'));
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Help & Support'), findsNWidgets(2)); // One in list, one in dialog
      expect(find.text('Need help? Contact us:'), findsOneWidget);
      expect(find.text('📧 support@pafar.com'), findsOneWidget);
      expect(find.text('📞 +1 (555) 123-4567'), findsOneWidget);
    });

    testWidgets('should show success message when settings are saved', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();
      
      // Toggle a switch to trigger save
      final biometricSwitch = find.widgetWithText(ListTile, 'Biometric Authentication');
      await tester.tap(biometricSwitch);
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Settings saved'), findsOneWidget);
    });

    testWidgets('should display loading indicator initially', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert - Before pumpAndSettle, should show loading
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('should display correct theme mode text', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('System'), findsOneWidget); // Default theme mode
    });

    testWidgets('should display correct language text', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('English'), findsOneWidget); // Default language
    });

    testWidgets('should have proper icons for each setting', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.byIcon(Icons.palette_outlined), findsOneWidget);
      expect(find.byIcon(Icons.language_outlined), findsOneWidget);
      expect(find.byIcon(Icons.fingerprint), findsOneWidget);
      expect(find.byIcon(Icons.lock_clock), findsOneWidget);
      expect(find.byIcon(Icons.location_on_outlined), findsOneWidget);
      expect(find.byIcon(Icons.bug_report_outlined), findsOneWidget);
      expect(find.byIcon(Icons.info_outline), findsOneWidget);
      expect(find.byIcon(Icons.privacy_tip_outlined), findsOneWidget);
      expect(find.byIcon(Icons.description_outlined), findsOneWidget);
      expect(find.byIcon(Icons.help_outline), findsOneWidget);
    });
  });
}