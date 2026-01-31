import React, { useState, useEffect } from 'react';
import {
    StyleSheet,
    View,
    Text,
    FlatList,
    ScrollView,
    TouchableOpacity,
    Image,
    Dimensions,
    StatusBar,
    SafeAreaView
} from 'react-native';
import { BlurView } from 'expo-blur';

const { width } = Dimensions.get('window');

/**
 * HollowScan Professional Home Screen
 * Rebranded with Electric Blue & Purple Palette
 */
const HomeScreen = ({ isDarkMode }) => {
    const [selectedCountry, setSelectedCountry] = useState('ALL');

    const countries = ['ALL', 'US', 'UK', 'EU', 'CA', 'DE', 'FR'];

    // HOLLOWSCAN BRAND COLORS (Extracted from Hollowscan.png)
    const brand = {
        blue: '#2D82FF',      // Electric Blue
        purple: '#9B4DFF',    // Vibrant Purple
        darkBg: '#0A0A0B',    // Ultra Dark Blue/Black
        lightBg: '#F8F9FE',   // Clean Airy White
    };

    const colors = isDarkMode ? {
        bg: brand.darkBg,
        card: '#161618',
        text: '#FFFFFF',
        textSecondary: '#8E8E93',
        accent: brand.blue,
        gradient: [brand.blue, brand.purple],
        tabActive: brand.blue,
        tabInactive: '#1C1C1E',
        border: '#2C2C2E'
    } : {
        bg: brand.lightBg,
        card: '#FFFFFF',
        text: '#1C1C1E',
        textSecondary: '#636366',
        accent: brand.blue,
        gradient: [brand.blue, brand.purple],
        tabActive: brand.blue,
        tabInactive: '#E5E5EA',
        border: '#D1D1D6'
    };

    const renderProductCard = ({ item }) => (
        <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
            <View style={styles.imageContainer}>
                <Image source={{ uri: item.image }} style={styles.productImage} />
                {/* PROFIT BADGE - HOLLOWSCAN GRADIENT STYLE */}
                <View style={[styles.badge, { backgroundColor: brand.blue }]}>
                    <Text style={styles.badgeText}>+{item.profit}% ROI</Text>
                </View>
            </View>

            <View style={styles.cardContent}>
                <View style={styles.titleRow}>
                    <Text style={[styles.title, { color: colors.text }]} numberOfLines={1}>{item.title}</Text>
                    <Text style={[styles.category, { color: colors.accent }]}>{item.category}</Text>
                </View>

                <View style={styles.priceRow}>
                    <View>
                        <Text style={[styles.priceLabel, { color: colors.textSecondary }]}>RETAIL</Text>
                        <Text style={[styles.priceValue, { color: colors.text }]}>${item.price}</Text>
                    </View>
                    <View style={styles.priceDivider} />
                    <View>
                        <Text style={[styles.priceLabel, { color: colors.textSecondary }]}>EST. RESALE</Text>
                        <Text style={[styles.priceValue, { color: brand.purple, fontWeight: '800' }]}>${item.resell}</Text>
                    </View>
                </View>

                <TouchableOpacity style={[styles.buyButton, { backgroundColor: colors.tabInactive, borderColor: colors.border, borderWidth: 1 }]}>
                    <Text style={[styles.buyButtonText, { color: colors.text }]}>VIEW DETAILS</Text>
                </TouchableOpacity>
            </View>

            {/* FREEMIUM OVERLAY */}
            {item.isLocked && (
                <BlurView intensity={60} tint={isDarkMode ? 'dark' : 'light'} style={styles.lockOverlay}>
                    <View style={styles.lockContent}>
                        <View style={[styles.lockCircle, { backgroundColor: isDarkMode ? '#FFF' : '#000' }]}>
                            <Text style={{ fontSize: 24 }}>🔒</Text>
                        </View>
                        <Text style={[styles.lockTitle, { color: colors.text }]}>Locked Product</Text>
                        <Text style={[styles.lockSub, { color: colors.textSecondary }]}>Upgrade to HollowScan Pro to unlock</Text>
                        <TouchableOpacity style={[styles.subscribeBtn, { backgroundColor: brand.blue }]}>
                            <Text style={styles.subscribeBtnText}>GET UNLIMITED ACCESS</Text>
                        </TouchableOpacity>
                    </View>
                </BlurView>
            )}
        </View>
    );

    return (
        <SafeAreaView style={[styles.container, { backgroundColor: colors.bg }]}>
            <StatusBar barStyle={isDarkMode ? 'light-content' : 'dark-content'} />

            {/* BRAND HEADER */}
            <View style={styles.header}>
                <View style={styles.headerTop}>
                    <Text style={[styles.headerTitle, { color: colors.text }]}>HOLLOW<Text style={{ color: brand.blue }}>SCAN</Text></Text>
                    <TouchableOpacity style={[styles.profileIcon, { backgroundColor: colors.tabInactive }]}>
                        <Text>👤</Text>
                    </TouchableOpacity>
                </View>
            </View>

            {/* COUNTRY TABS */}
            <View style={styles.tabWrapper}>
                <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabsScroll}>
                    {countries.map(c => (
                        <TouchableOpacity
                            key={c}
                            onPress={() => setSelectedCountry(c)}
                            style={[
                                styles.tab,
                                { backgroundColor: selectedCountry === c ? brand.blue : colors.tabInactive }
                            ]}
                        >
                            <Text style={[styles.tabText, { color: selectedCountry === c ? '#FFF' : colors.textSecondary }]}>
                                {c}
                            </Text>
                        </TouchableOpacity>
                    ))}
                </ScrollView>
            </View>

            {/* FEED */}
            <FlatList
                data={[
                    { id: '1', title: 'Jordan 4 Retro SB', category: 'SNEAKERS', price: 210, resell: 450, profit: 114, isLocked: false, image: 'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&q=80&w=400' },
                    { id: '2', title: 'iPhone 15 Pro Max', category: 'ELECTRONICS', price: 1199, resell: 1450, profit: 21, isLocked: true, image: 'https://images.unsplash.com/photo-1696446701796-da61225697cc?auto=format&fit=crop&q=80&w=400' }
                ]}
                keyExtractor={item => item.id}
                renderItem={renderProductCard}
                contentContainerStyle={styles.feedScroll}
                showsVerticalScrollIndicator={false}
            />
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1 },
    header: { paddingHorizontal: 20, paddingTop: 10, marginBottom: 15 },
    headerTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    headerTitle: { fontSize: 24, fontWeight: '900', letterSpacing: -1 },
    profileIcon: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center' },
    tabWrapper: { height: 40, marginBottom: 15 },
    tabsScroll: { paddingHorizontal: 20 },
    tab: {
        paddingHorizontal: 22,
        height: 38,
        borderRadius: 12,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 8
    },
    tabText: { fontWeight: '700', fontSize: 13, letterSpacing: 0.5 },
    feedScroll: { paddingHorizontal: 20, paddingBottom: 100 },
    card: {
        width: '100%',
        borderRadius: 24,
        marginBottom: 20,
        overflow: 'hidden',
        borderWidth: 1
    },
    imageContainer: { width: '100%', height: 220 },
    productImage: { width: '100%', height: '100%', resizeMode: 'cover' },
    badge: {
        position: 'absolute',
        top: 15,
        left: 15,
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 10
    },
    badgeText: { color: '#FFF', fontWeight: '900', fontSize: 11 },
    cardContent: { padding: 18 },
    titleRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
    title: { fontSize: 18, fontWeight: '800', flex: 1, marginRight: 10 },
    category: { fontSize: 10, fontWeight: '900', letterSpacing: 1 },
    priceRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 20 },
    priceLabel: { fontSize: 9, fontWeight: '700', letterSpacing: 0.5, marginBottom: 2 },
    priceValue: { fontSize: 18, fontWeight: '700' },
    priceDivider: { width: 1, height: 25, backgroundColor: '#333', mx: 20, opacity: 0.2, marginHorizontal: 20 },
    buyButton: {
        height: 50,
        borderRadius: 15,
        justifyContent: 'center',
        alignItems: 'center'
    },
    buyButtonText: { fontWeight: '800', fontSize: 14, letterSpacing: 1 },
    lockOverlay: { ...StyleSheet.absoluteFillObject, justifyContent: 'center', alignItems: 'center' },
    lockContent: { alignItems: 'center', padding: 20, borderRadius: 30 },
    lockCircle: { width: 60, height: 60, borderRadius: 30, justifyContent: 'center', alignItems: 'center', marginBottom: 15 },
    lockTitle: { fontSize: 20, fontWeight: '900', marginBottom: 5 },
    lockSub: { fontSize: 14, textAlign: 'center', marginBottom: 25 },
    subscribeBtn: {
        paddingHorizontal: 30,
        paddingVertical: 15,
        borderRadius: 15,
        shadowColor: '#00D09C',
        shadowOpacity: 0.3,
        shadowRadius: 10
    },
    subscribeBtnText: { color: '#FFF', fontWeight: '900', fontSize: 13, letterSpacing: 1 }
});

export default HomeScreen;
