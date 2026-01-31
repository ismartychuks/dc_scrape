import React, { useContext, useState, useEffect } from 'react';
import { StyleSheet, View, Text, ScrollView, TouchableOpacity, Image, Switch, Modal, TextInput, ActivityIndicator, Linking, Alert, Clipboard } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { BlurView } from 'expo-blur';
import { LinearGradient } from 'expo-linear-gradient';
import { SavedContext } from '../context/SavedContext';
import { UserContext } from '../context/UserContext';
import Constants from '../Constants';
import { registerForPushNotifications, requestNotificationPermissions } from '../services/PushNotificationService';

const ProfileScreen = () => {
    const { savedProducts } = useContext(SavedContext);
    const { user } = useContext(UserContext);
    const brand = Constants.BRAND;

    // State Management
    const [notificationsEnabled, setNotificationsEnabled] = useState(true);
    const [darkMode, setDarkMode] = useState(false);
    const [country, setCountry] = useState('US');
    const [telegramLinked, setTelegramLinked] = useState(false);
    const [telegramModalVisible, setTelegramModalVisible] = useState(false);
    const [telegramLinkKey, setTelegramLinkKey] = useState(null);
    const [isGeneratingKey, setIsGeneratingKey] = useState(false);
    const [isCheckingStatus, setIsCheckingStatus] = useState(false);
    const [countryModalVisible, setCountryModalVisible] = useState(false);
    const [isPremium, setIsPremium] = useState(false);
    const [premiumUntil, setPremiumUntil] = useState(null);
    const userId = user?.id || 'guest-user';

    // Calculate generic stats
    const savedCount = savedProducts.length;
    const potentialProfit = savedProducts.reduce((acc, p) => {
        const buy = parseFloat(p.product_data?.price || 0);
        const sell = parseFloat(p.product_data?.resell || 0);
        const fees = sell * 0.15;
        const profit = sell - buy - fees;
        return acc + (profit > 0 ? profit : 0);
    }, 0).toFixed(0);

    // Handlers
    const handleGenerateLinkKey = async () => {
        if (!userId || userId === 'guest-user') {
            Alert.alert('Error', 'User ID not found. Please restart the app.');
            return;
        }

        setIsGeneratingKey(true);
        try {
            console.log('[TELEGRAM] Generating link key for user:', userId);
            
            const response = await fetch(
                `${Constants.API_BASE_URL}/v1/user/telegram/generate-key?user_id=${userId}`,
                { method: 'POST', headers: { 'Content-Type': 'application/json' } }
            );

            const data = await response.json();
            if (data.success) {
                setTelegramLinkKey(data.link_key);
            } else {
                Alert.alert('Error', data.detail || 'Failed to generate link key');
                setTelegramModalVisible(false);
            }
        } catch (error) {
            console.error('[TELEGRAM] Error:', error);
            Alert.alert('Error', `Failed to generate link key: ${error.message}`);
            setTelegramModalVisible(false);
        } finally {
            setIsGeneratingKey(false);
        }
    };

    const handleCheckLinkStatus = async () => {
        setIsCheckingStatus(true);
        try {
            console.log('[TELEGRAM] Checking link status...');
            
            const response = await fetch(
                `${Constants.API_BASE_URL}/v1/user/telegram/link-status?user_id=${userId}`,
                { method: 'GET', headers: { 'Content-Type': 'application/json' } }
            );

            const data = await response.json();
            if (data.success && data.linked) {
                setTelegramLinked(true);
                setIsPremium(data.is_premium || false);
                setPremiumUntil(data.premium_until);
                setTelegramLinkKey(null);
            } else {
                Alert.alert('⏳ Not Linked Yet', 'Send the command to the bot first, then try again.');
            }
        } catch (error) {
            console.error('[TELEGRAM] Error:', error);
            Alert.alert('Error', `Failed to check status: ${error.message}`);
        } finally {
            setIsCheckingStatus(false);
        }
    };

    const handleTelegramUnlink = () => {
        Alert.alert(
            'Unlink Telegram?',
            'You will stop receiving Telegram notifications',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Unlink',
                    style: 'destructive',
                    onPress: () => {
                        setTelegramLinked(false);
                        Alert.alert('Unlinked', 'Your Telegram account has been unlinked');
                    }
                }
            ]
        );
    };

    const openTelegramBot = () => {
        Linking.openURL('https://t.me/Hollowscan_bot').catch(() => {
            Alert.alert('Error', 'Could not open Telegram. Please install Telegram first.');
        });
    };

    const handleNotificationsToggle = async (value) => {
        if (value) {
            // Enable notifications - request permissions
            const hasPermission = await requestNotificationPermissions();
            if (hasPermission) {
                setNotificationsEnabled(true);
                Alert.alert('Notifications Enabled', 'You will now receive push notifications for new deals!');
                console.log('[NOTIFICATIONS] Enabled');
            } else {
                Alert.alert(
                    'Permission Required',
                    'Please enable notifications in your system settings to receive deal alerts.'
                );
                console.log('[NOTIFICATIONS] Permission denied');
            }
        } else {
            // Disable notifications
            setNotificationsEnabled(false);
            Alert.alert('Notifications Disabled', 'You will not receive push notifications.');
            console.log('[NOTIFICATIONS] Disabled');
        }
    };
    const StatBox = ({ label, value }) => (
        <View style={styles.statBox}>
            <Text style={styles.statValue}>{value}</Text>
            <Text style={styles.statLabel}>{label}</Text>
        </View>
    );

    const SettingRowWithSwitch = ({ icon, label, value, onValueChange }) => (
        <View style={styles.settingRow}>
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <Text style={{ marginRight: 15, fontSize: 18, width: 25, textAlign: 'center' }}>{icon}</Text>
                <Text style={styles.settingLabel}>{label}</Text>
            </View>
            <Switch
                value={value}
                onValueChange={onValueChange}
                trackColor={{ false: '#D1D5DB', true: '#FF8A65' }}
                thumbColor={value ? '#FF6B35' : '#F3F4F6'}
            />
        </View>
    );

    const SettingRow = ({ icon, label, value, onPress, isDestructive, status }) => (
        <TouchableOpacity style={styles.settingRow} onPress={onPress} disabled={!onPress}>
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <Text style={{ marginRight: 15, fontSize: 18, width: 25, textAlign: 'center' }}>{icon}</Text>
                <View>
                    <Text style={[styles.settingLabel, isDestructive && { color: '#EF4444' }]}>{label}</Text>
                    {status && <Text style={styles.statusText}>{status}</Text>}
                </View>
            </View>
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                {value && <Text style={[styles.settingValue, isDestructive && { color: '#EF4444' }]}>{value}</Text>}
                {onPress && <Text style={{ color: '#D1D5DB', fontSize: 16, marginLeft: 10 }}>›</Text>}
            </View>
        </TouchableOpacity>
    );

    const SectionHeader = ({ title }) => (
        <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>{title}</Text>
        </View>
    );

    return (
        <SafeAreaView style={styles.container} edges={['top']}>
            <ScrollView contentContainerStyle={styles.scroll}>
                {/* PROFILE HEADER */}
                <LinearGradient colors={['#FF8A65', '#FF6B35']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.profileHeader}>
                    <View style={styles.avatarContainer}>
                        <Text style={styles.avatarText}>H</Text>
                    </View>
                    <Text style={styles.userName}>HollowScan User</Text>
                    <View style={styles.planBadge}>
                        <Text style={styles.planText}>👑 Free Plan</Text>
                    </View>
                    <TouchableOpacity style={styles.upgradeBtn}>
                        <LinearGradient colors={['#FF6B35', '#FF5722']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.upgradeGradient}>
                            <Text style={styles.upgradeText}>Upgrade to Premium</Text>
                        </LinearGradient>
                    </TouchableOpacity>
                </LinearGradient>

                {/* STATS ROW */}
                <View style={styles.statsRow}>
                    <StatBox label="Saved" value={savedCount} />
                    <StatBox label="Profit" value={`$${potentialProfit}`} />
                    <StatBox label="Alerts" value="3" />
                </View>

                {/* NOTIFICATION & PREFERENCES */}
                <SectionHeader title="SETTINGS" />
                <View style={styles.group}>
                    <SettingRowWithSwitch
                        icon="🔔"
                        label="Push Notifications"
                        value={notificationsEnabled}
                        onValueChange={handleNotificationsToggle}
                    />
                    <SettingRowWithSwitch
                        icon="🌙"
                        label="Dark Mode"
                        value={darkMode}
                        onValueChange={setDarkMode}
                    />
                    <SettingRow
                        icon="🌍"
                        label="Preferred Country"
                        value={country}
                        status="Region for deals"
                        onPress={() => setCountryModalVisible(true)}
                    />
                </View>

                {/* INTEGRATIONS */}
                <SectionHeader title="INTEGRATIONS" />
                <View style={styles.group}>
                    <SettingRow
                        icon="📱"
                        label="Telegram Bot"
                        value={telegramLinked ? '✓ Linked' : 'Not linked'}
                        status={
                            isPremium 
                                ? `👑 Premium until ${new Date(premiumUntil).toLocaleDateString()}`
                                : (telegramLinked ? 'Receiving notifications' : 'Connect for alerts')
                        }
                        onPress={() => setTelegramModalVisible(true)}
                    />
                </View>

                {/* ACCOUNT */}
                <SectionHeader title="ACCOUNT" />
                <View style={styles.group}>
                    <SettingRow icon="👤" label="Profile Information" onPress={() => {}} />
                    <SettingRow icon="🔒" label="Change Password" onPress={() => {}} />
                    <SettingRow icon="✉️" label="Email Verification" value="Verified" />
                </View>

                {/* SUPPORT */}
                <SectionHeader title="SUPPORT" />
                <View style={styles.group}>
                    <SettingRow icon="❓" label="Help & FAQ" onPress={() => {}} />
                    <SettingRow icon="📞" label="Contact Support" onPress={() => {}} />
                    <SettingRow icon="⭐" label="Rate the App" onPress={() => {}} />
                </View>

                {/* LEGAL */}
                <SectionHeader title="LEGAL" />
                <View style={styles.group}>
                    <SettingRow icon="📄" label="Terms of Service" onPress={() => {}} />
                    <SettingRow icon="🛡️" label="Privacy Policy" onPress={() => {}} />
                </View>

                {/* SIGN OUT */}
                <TouchableOpacity style={styles.signOutBtn}>
                    <Text style={styles.signOutText}>→ Sign Out</Text>
                </TouchableOpacity>

                <Text style={styles.version}>Version 1.0.0 (Build 1)</Text>
                <View style={{ height: 50 }} />
            </ScrollView>

            {/* TELEGRAM MODAL - SIMPLIFIED */}
            <Modal
                visible={telegramModalVisible}
                transparent={true}
                animationType="fade"
                onRequestClose={() => !isGeneratingKey && !isCheckingStatus && setTelegramModalVisible(false)}
            >
                <BlurView intensity={90} style={styles.blurContainer}>
                    <View style={styles.centeredView}>
                        <View style={styles.modalView}>
                            <View style={styles.modalHeader}>
                                <Text style={styles.modalTitle}>
                                    {telegramLinked ? '✅ Connected' : '📱 Connect Telegram'}
                                </Text>
                                <TouchableOpacity
                                    onPress={() => {
                                        setTelegramModalVisible(false);
                                        setTelegramLinkKey(null);
                                    }}
                                    disabled={isGeneratingKey || isCheckingStatus}
                                >
                                    <Text style={styles.closeBtn}>✕</Text>
                                </TouchableOpacity>
                            </View>

                            {!telegramLinked ? (
                                <>
                                    {!telegramLinkKey ? (
                                        // Step 1: Start
                                        <>
                                            <Text style={styles.modalDescription}>
                                                Get instant notifications for new deals
                                            </Text>

                                            <TouchableOpacity
                                                style={[styles.primaryBtn, isGeneratingKey && { opacity: 0.6 }]}
                                                onPress={handleGenerateLinkKey}
                                                disabled={isGeneratingKey}
                                            >
                                                {isGeneratingKey ? (
                                                    <ActivityIndicator color="#fff" size="small" />
                                                ) : (
                                                    <Text style={styles.primaryBtnText}>Generate Link Key</Text>
                                                )}
                                            </TouchableOpacity>
                                        </>
                                    ) : (
                                        // Step 2: Show Key & Bot Link
                                        <>
                                            <View style={styles.keyBox}>
                                                <Text style={styles.keyLabel}>Your Code:</Text>
                                                <Text style={styles.keyText}>{telegramLinkKey}</Text>
                                                <TouchableOpacity
                                                    style={styles.copyBtn}
                                                    onPress={() => {
                                                        Clipboard.setString(telegramLinkKey);
                                                        Alert.alert('✓ Copied', 'Code copied!');
                                                    }}
                                                >
                                                    <Text style={styles.copyBtnText}>Copy Code</Text>
                                                </TouchableOpacity>
                                            </View>

                                            <TouchableOpacity
                                                style={styles.botLinkBtn}
                                                onPress={openTelegramBot}
                                            >
                                                <Text style={styles.botLinkText}>🤖 Open Bot</Text>
                                            </TouchableOpacity>

                                            <Text style={{ textAlign: 'center', color: '#6B7280', fontSize: 12, marginBottom: 20 }}>
                                                Send: <Text style={{ fontWeight: '700' }}>/link {telegramLinkKey}</Text>
                                            </Text>

                                            <View style={styles.modalButtonsContainer}>
                                                <TouchableOpacity
                                                    style={styles.cancelBtn}
                                                    onPress={() => setTelegramLinkKey(null)}
                                                    disabled={isCheckingStatus}
                                                >
                                                    <Text style={styles.cancelBtnText}>Back</Text>
                                                </TouchableOpacity>
                                                <TouchableOpacity
                                                    style={styles.linkBtn}
                                                    onPress={handleCheckLinkStatus}
                                                    disabled={isCheckingStatus}
                                                >
                                                    {isCheckingStatus ? (
                                                        <ActivityIndicator color="#fff" size="small" />
                                                    ) : (
                                                        <Text style={styles.linkBtnText}>Verify</Text>
                                                    )}
                                                </TouchableOpacity>
                                            </View>
                                        </>
                                    )}
                                </>
                            ) : (
                                <>
                                    <View style={styles.successContainer}>
                                        <Text style={styles.successEmoji}>🎉</Text>
                                        <Text style={styles.successText}>Connected!</Text>
                                        {isPremium && (
                                            <Text style={{ fontSize: 12, color: '#D97706', marginTop: 5 }}>👑 Premium Status Synced</Text>
                                        )}
                                    </View>

                                    <View style={styles.benefitsContainer}>
                                        <Text style={styles.benefitTitle}>Getting notifications for:</Text>
                                        <Text style={styles.benefit}>✓ New deals</Text>
                                        <Text style={styles.benefit}>✓ Price drops</Text>
                                        <Text style={styles.benefit}>✓ High ROI items</Text>
                                    </View>

                                    <View style={styles.modalButtonsContainer}>
                                        <TouchableOpacity
                                            style={styles.unlinkBtn}
                                            onPress={handleTelegramUnlink}
                                        >
                                            <Text style={styles.unlinkBtnText}>Disconnect</Text>
                                        </TouchableOpacity>
                                        <TouchableOpacity
                                            style={styles.doneBtn}
                                            onPress={() => setTelegramModalVisible(false)}
                                        >
                                            <Text style={styles.doneBtnText}>Done</Text>
                                        </TouchableOpacity>
                                    </View>
                                </>
                            )}
                        </View>
                    </View>
                </BlurView>
            </Modal>

            {/* COUNTRY SELECTOR MODAL */}
            <Modal
                visible={countryModalVisible}
                transparent={true}
                animationType="fade"
                onRequestClose={() => setCountryModalVisible(false)}
            >
                <BlurView intensity={90} style={styles.blurContainer}>
                    <View style={styles.centeredView}>
                        <View style={[styles.modalView, { width: '80%', maxWidth: 300 }]}>
                            <Text style={styles.modalTitle}>Select Country</Text>
                            {['US', 'UK', 'CA'].map(c => (
                                <TouchableOpacity
                                    key={c}
                                    style={[
                                        styles.countryOption,
                                        country === c && styles.countryOptionActive
                                    ]}
                                    onPress={() => {
                                        setCountry(c);
                                        setCountryModalVisible(false);
                                    }}
                                >
                                    <Text style={[
                                        styles.countryOptionText,
                                        country === c && styles.countryOptionTextActive
                                    ]}>
                                        {c === 'US' ? '🇺🇸 United States' : c === 'UK' ? '🇬🇧 United Kingdom' : '🇨🇦 Canada'}
                                    </Text>
                                </TouchableOpacity>
                            ))}
                        </View>
                    </View>
                </BlurView>
            </Modal>
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#FAFAF8' },
    scroll: { paddingBottom: 40 },

    // Profile Header
    profileHeader: {
        alignItems: 'center',
        padding: 30,
        paddingBottom: 40,
    },
    avatarContainer: {
        width: 80,
        height: 80,
        borderRadius: 40,
        backgroundColor: 'rgba(255,255,255,0.3)',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 10,
        shadowColor: '#000',
        shadowOpacity: 0.1,
        shadowRadius: 10,
    },
    avatarText: { fontSize: 32, color: '#FFF', fontWeight: '800' },
    userName: { fontSize: 20, fontWeight: '800', color: '#FFF', marginBottom: 5 },
    planBadge: {
        backgroundColor: 'rgba(255,255,255,0.2)',
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 12,
        marginBottom: 15,
    },
    planText: { fontSize: 12, fontWeight: '600', color: '#FFF' },
    upgradeBtn: {
        overflow: 'hidden',
        borderRadius: 25,
        shadowColor: '#000',
        shadowOpacity: 0.2,
        shadowRadius: 10,
    },
    upgradeGradient: {
        paddingHorizontal: 40,
        paddingVertical: 12,
        alignItems: 'center',
        justifyContent: 'center',
    },
    upgradeText: { color: '#FFF', fontWeight: '700', fontSize: 15 },

    // Stats
    statsRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        padding: 20,
        marginTop: -15,
        paddingHorizontal: 10,
    },
    statBox: {
        flex: 1,
        backgroundColor: '#FFF',
        padding: 15,
        borderRadius: 16,
        alignItems: 'center',
        marginHorizontal: 5,
        shadowColor: '#000',
        shadowOpacity: 0.05,
        shadowRadius: 5,
        elevation: 2,
    },
    statValue: { fontSize: 18, fontWeight: '800', color: '#1F2937', marginBottom: 2 },
    statLabel: { fontSize: 12, fontWeight: '600', color: '#9CA3AF' },

    // Sections
    sectionHeader: { paddingHorizontal: 20, marginTop: 20, marginBottom: 8 },
    sectionTitle: { fontSize: 12, fontWeight: '800', color: '#9CA3AF', letterSpacing: 1 },

    // Groups
    group: {
        backgroundColor: '#FFF',
        borderTopWidth: 1,
        borderBottomWidth: 1,
        borderColor: '#F3F4F6',
        marginHorizontal: 10,
        marginBottom: 10,
        borderRadius: 12,
        overflow: 'hidden',
    },
    settingRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 16,
        paddingLeft: 20,
        paddingRight: 20,
        borderBottomWidth: 1,
        borderBottomColor: '#F3F4F6',
    },
    settingLabel: { fontSize: 16, fontWeight: '500', color: '#374151' },
    statusText: { fontSize: 12, color: '#9CA3AF', marginTop: 4 },
    settingValue: { color: '#9CA3AF', fontSize: 14 },

    // Sign Out
    signOutBtn: {
        marginHorizontal: 20,
        marginTop: 15,
        marginBottom: 20,
        backgroundColor: '#FEF2F2',
        padding: 15,
        borderRadius: 12,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#FECACA',
    },
    signOutText: { color: '#EF4444', fontWeight: '700', fontSize: 16 },
    version: { textAlign: 'center', color: '#D1D5DB', fontSize: 12 },

    // Modal Styles
    blurContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    centeredView: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    modalView: {
        backgroundColor: '#FFF',
        borderRadius: 20,
        padding: 25,
        width: '90%',
        maxWidth: 400,
        shadowColor: '#000',
        shadowOpacity: 0.25,
        shadowRadius: 4,
        elevation: 5,
    },
    modalHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 15,
    },
    modalTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: '#1F2937',
    },
    closeBtn: {
        fontSize: 24,
        color: '#9CA3AF',
    },
    modalDescription: {
        fontSize: 14,
        color: '#6B7280',
        marginBottom: 20,
        lineHeight: 20,
    },

    // Telegram Modal
    botLinkBtn: {
        backgroundColor: '#0EA5E9',
        padding: 15,
        borderRadius: 12,
        alignItems: 'center',
        marginBottom: 20,
    },
    botLinkText: {
        color: '#FFF',
        fontWeight: '700',
        fontSize: 16,
    },
    orDivider: {
        textAlign: 'center',
        color: '#D1D5DB',
        fontSize: 12,
        marginBottom: 15,
        fontWeight: '600',
    },
    telegramInput: {
        borderWidth: 1,
        borderColor: '#E5E7EB',
        borderRadius: 10,
        padding: 12,
        fontSize: 14,
        marginBottom: 20,
        color: '#1F2937',
    },
    modalButtonsContainer: {
        flexDirection: 'row',
        gap: 10,
    },
    cancelBtn: {
        flex: 1,
        padding: 12,
        borderRadius: 10,
        backgroundColor: '#F3F4F6',
        alignItems: 'center',
    },
    cancelBtnText: {
        color: '#6B7280',
        fontWeight: '700',
        fontSize: 15,
    },
    linkBtn: {
        flex: 1,
        padding: 12,
        borderRadius: 10,
        backgroundColor: '#FF8A65',
        alignItems: 'center',
        justifyContent: 'center',
    },
    linkBtnText: {
        color: '#FFF',
        fontWeight: '700',
        fontSize: 15,
    },
    unlinkBtn: {
        flex: 1,
        padding: 12,
        borderRadius: 10,
        backgroundColor: '#FEE2E2',
        alignItems: 'center',
    },
    unlinkBtnText: {
        color: '#DC2626',
        fontWeight: '700',
        fontSize: 15,
    },
    doneBtn: {
        flex: 1,
        padding: 12,
        borderRadius: 10,
        backgroundColor: '#10B981',
        alignItems: 'center',
    },
    doneBtnText: {
        color: '#FFF',
        fontWeight: '700',
        fontSize: 15,
    },

    // Success State
    successContainer: {
        alignItems: 'center',
        marginBottom: 25,
    },
    successEmoji: {
        fontSize: 48,
        marginBottom: 10,
    },
    successText: {
        fontSize: 16,
        fontWeight: '700',
        color: '#1F2937',
    },
    benefitsContainer: {
        backgroundColor: '#F0FDF4',
        padding: 15,
        borderRadius: 10,
        marginBottom: 20,
    },
    benefitTitle: {
        fontSize: 14,
        fontWeight: '700',
        color: '#1F2937',
        marginBottom: 10,
    },
    benefit: {
        fontSize: 13,
        color: '#059669',
        marginVertical: 4,
    },

    // Country Modal
    countryOption: {
        padding: 15,
        borderBottomWidth: 1,
        borderBottomColor: '#F3F4F6',
        borderRadius: 8,
        marginVertical: 5,
        backgroundColor: '#F9FAFB',
    },
    countryOptionActive: {
        backgroundColor: '#FF8A65',
    },
    countryOptionText: {
        fontSize: 16,
        color: '#374151',
        fontWeight: '500',
    },
    countryOptionTextActive: {
        color: '#FFF',
        fontWeight: '700',
    },

    // Telegram Link Key Generation
    stepContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 20,
        paddingBottom: 15,
        borderBottomWidth: 1,
        borderBottomColor: '#E5E7EB',
    },
    stepNumber: {
        fontSize: 20,
        fontWeight: '800',
        color: '#FF8A65',
        marginRight: 12,
        backgroundColor: '#FFF3E0',
        width: 40,
        height: 40,
        borderRadius: 20,
        textAlign: 'center',
        textAlignVertical: 'center',
    },
    stepText: {
        fontSize: 16,
        fontWeight: '700',
        color: '#1F2937',
        flex: 1,
    },
    primaryBtn: {
        backgroundColor: '#FF8A65',
        padding: 14,
        borderRadius: 10,
        alignItems: 'center',
        marginBottom: 20,
    },
    primaryBtnText: {
        color: '#FFF',
        fontWeight: '700',
        fontSize: 15,
    },
    infoBox: {
        backgroundColor: '#FFF3E0',
        padding: 15,
        borderRadius: 10,
        marginBottom: 15,
        borderLeftWidth: 4,
        borderLeftColor: '#FF8A65',
    },
    infoTitle: {
        fontSize: 13,
        fontWeight: '700',
        color: '#E65100',
        marginBottom: 8,
    },
    infoText: {
        fontSize: 12,
        color: '#BF360C',
        marginVertical: 3,
        lineHeight: 18,
    },
    keyDisplay: {
        backgroundColor: '#F9FAFB',
        padding: 15,
        borderRadius: 12,
        marginBottom: 15,
    },
    keyLabel: {
        fontSize: 11,
        fontWeight: '700',
        color: '#9CA3AF',
        marginBottom: 8,
        textTransform: 'uppercase',
        letterSpacing: 0.5,
    },
    keyBox: {
        backgroundColor: '#F9FAFB',
        padding: 15,
        borderRadius: 10,
        marginBottom: 15,
        borderWidth: 1,
        borderColor: '#E5E7EB',
        alignItems: 'center',
    },
    keyText: {
        fontSize: 28,
        fontWeight: '800',
        color: '#FF8A65',
        letterSpacing: 2,
        marginBottom: 12,
    },
    copyBtn: {
        backgroundColor: '#FFF',
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 6,
        borderWidth: 1,
        borderColor: '#E5E7EB',
    },
    copyBtnText: {
        color: '#374151',
        fontWeight: '600',
        fontSize: 12,
    },
    instructionBox: {
        backgroundColor: '#F0F9FF',
        padding: 12,
        borderRadius: 10,
        marginBottom: 15,
        borderLeftWidth: 4,
        borderLeftColor: '#0EA5E9',
    },
    instructionTitle: {
        fontSize: 11,
        fontWeight: '700',
        color: '#0369A1',
        marginBottom: 8,
    },
    commandBox: {
        backgroundColor: '#FFF',
        padding: 10,
        borderRadius: 6,
        borderWidth: 1,
        borderColor: '#E0F2FE',
    },
    commandText: {
        fontSize: 13,
        fontFamily: 'monospace',
        fontWeight: '600',
        color: '#0369A1',
    },
});

export default ProfileScreen;
