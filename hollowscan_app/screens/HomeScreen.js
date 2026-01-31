import React, { useState, useEffect, useCallback, useContext } from 'react';
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
    Modal,
    ActivityIndicator,
    TextInput,
    Linking,
    Animated,
    PanResponder
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { BlurView } from 'expo-blur';
import { LinearGradient } from 'expo-linear-gradient';
import Constants from '../Constants';
import { SavedContext } from '../context/SavedContext';
import LiveProductService from '../services/LiveProductService';
import { setupNotificationHandler, sendDealNotification } from '../services/PushNotificationService';

const { width, height } = Dimensions.get('window');

const getRelativeTime = (dateString) => {
    if (!dateString) return 'Just now';
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
    return date.toLocaleDateString();
};

const HomeScreen = ({ isDarkMode }) => {
    const navigation = useNavigation();

    // CONFIG
    const LIMIT = 10;
    const USER_ID = '8923304e-657e-4e7e-800a-94e7248ecf7f';

    // REGIONS - Use full region names
    const regions = [
        { id: 'USA Stores', label: 'USA', flag: '🇺🇸' },
        { id: 'UK Stores', label: 'UK', flag: '🇬🇧' },
        { id: 'Canada Stores', label: 'CA', flag: '🇨🇦' }
    ];

    // STATE
    const [selectedRegion, setSelectedRegion] = useState('USA Stores');
    const [selectedSub, setSelectedSub] = useState('ALL');
    const [selectedCategories, setSelectedCategories] = useState(['ALL']); // Multiple selection
    const [searchQuery, setSearchQuery] = useState('');
    const [isFilterVisible, setFilterVisible] = useState(false);

    const [dynamicCategories, setDynamicCategories] = useState({});
    const [alerts, setAlerts] = useState([]);
    const [quota, setQuota] = useState({ used: 0, limit: 4 });

    const [isLoading, setIsLoading] = useState(false);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [offset, setOffset] = useState(0);
    const [hasMore, setHasMore] = useState(true);

    // BRAND
    const brand = Constants.BRAND;
    const colors = isDarkMode ? {
        bg: brand.DARK_BG,
        card: '#161618',
        text: '#FFFFFF',
        textSecondary: '#8E8E93',
        accent: brand.BLUE,
        tabInactive: '#1C1C1E',
        border: 'rgba(255,255,255,0.08)',
        input: '#1C1C1E',
        badgeBg: 'rgba(45, 130, 255, 0.15)'
    } : {
        bg: brand.LIGHT_BG,
        card: '#FFFFFF',
        text: '#1C1C1E',
        textSecondary: '#636366',
        accent: brand.BLUE,
        tabInactive: '#FFFFFF',
        border: 'rgba(0,0,0,0.05)',
        input: '#FFFFFF',
        badgeBg: '#E0F2FE'
    };

    // INITIAL FETCH
    useEffect(() => {
        fetchInitialData();
    }, [selectedRegion, selectedCategories]);

    // SETUP NOTIFICATIONS & LIVE UPDATES
    useEffect(() => {
        console.log('[HOME] Setting up notifications and live updates');
        
        // Setup notification handler
        setupNotificationHandler();

        // Reset product time when region/category changes
        LiveProductService.resetLastProductTime();

        // Start polling for new products
        LiveProductService.startPolling({
            userId: USER_ID,
            country: selectedRegion,
            category: selectedCategories.includes('ALL') ? 'ALL' : selectedCategories[0],
            onlyNew: true,
        });

        // Subscribe to new products
        const unsubscribe = LiveProductService.subscribe((newProducts) => {
            console.log('[HOME] Received', newProducts.length, 'new products');
            
            // Add new products to the TOP of the list
            setAlerts(prev => [...newProducts, ...prev]);

            // Send notification for each new product
            newProducts.forEach(product => {
                sendDealNotification(product);
            });
        });

        // Cleanup
        return () => {
            console.log('[HOME] Cleaning up live updates');
            unsubscribe();
            LiveProductService.stopPolling();
        };
    }, [selectedRegion, selectedCategories]);

    const fetchInitialData = async () => {
        setIsLoading(true);
        setOffset(0);
        setHasMore(true);

        await Promise.all([
            fetchCategories(),
            fetchUserStatus(),
            fetchAlerts(0, true)
        ]);

        setIsLoading(false);
    };

    const fetchCategories = async () => {
        try {
            const response = await fetch(`${Constants.API_BASE_URL}/v1/categories`);
            const data = await response.json();
            console.log('[CATEGORIES] Fetched data:', data);
            // New format: {US: [...], UK: [...], CA: [...]}
            setDynamicCategories(data || {});
        } catch (e) { 
            console.log("Cat Err:", e);
            // Set some defaults if fetch fails
            setDynamicCategories({
                US: [],
                UK: [],
                CA: []
            });
        }
    };

    const fetchUserStatus = async () => {
        try {
            const response = await fetch(`${Constants.API_BASE_URL}/v1/user/status?user_id=${USER_ID}`);
            const data = await response.json();
            setQuota({ used: data.views_used, limit: data.views_limit });
        } catch (e) { console.log("Quota Err:", e); }
    };

    const fetchAlerts = async (currentOffset, reset = false) => {
        try {
            // If 'ALL' is selected, send empty string; otherwise send first selected category
            const catParam = selectedCategories.includes('ALL') ? 'ALL' : selectedCategories[0] || 'ALL';
            const url = `${Constants.API_BASE_URL}/v1/feed?user_id=${USER_ID}&region=${encodeURIComponent(selectedRegion)}&category=${encodeURIComponent(catParam)}&offset=${currentOffset}&limit=${LIMIT}`;

            console.log('[FETCH] Sending request to:', url);
            console.log('[FETCH] Selected region:', selectedRegion);
            console.log('[FETCH] Selected categories:', selectedCategories);
            
            const response = await fetch(url);
            const data = await response.json();

            console.log('[FETCH] Response data count:', Array.isArray(data) ? data.length : 'Not array');

            if (Array.isArray(data)) {
                if (reset) {
                    setAlerts(data);
                } else {
                    setAlerts(prev => [...prev, ...data]);
                }
                setHasMore(data.length === LIMIT);
            }
        } catch (e) {
            console.log("Alert Fetch Err:", e);
        }
    };

    const handleLoadMore = () => {
        if (!hasMore || isLoadingMore || isLoading) return;
        setIsLoadingMore(true);
        const nextOffset = offset + LIMIT;
        setOffset(nextOffset);
        fetchAlerts(nextOffset).then(() => setIsLoadingMore(false));
    };

    const onRefresh = async () => {
        setIsRefreshing(true);
        await fetchInitialData();
        setIsRefreshing(false);
    };

    // Get subcategories for the selected region from the new format
    const currentSubcategories = [
        'ALL',
        ...(dynamicCategories[selectedRegion] || [])
    ];

    // Log available categories when they change
    useEffect(() => {
        console.log('[CATEGORIES] Available for', selectedRegion, ':', currentSubcategories);
    }, [currentSubcategories, selectedRegion]);

    const { toggleSave, isSaved } = useContext(SavedContext);

    // ... (existing helper functions like getRelativeTime) ...

    const renderProductCard = ({ item }) => {
        if (!item) return null;
        const data = item.product_data || {};
        const catName = (item.category_name || "PROMO").toUpperCase();
        const hasResell = data.resell && data.resell !== '0';
        const hasRoi = data.roi && data.roi !== '0';
        const saved = isSaved(item.id);

        return (
            <TouchableOpacity
                style={[styles.card, { borderColor: colors.border }]}
                onPress={() => navigation.navigate('ProductDetail', { product: item })}
                activeOpacity={0.9}
            >
                {/* GRADIENT OVERLAY ON CARD */}
                {isDarkMode && <View style={styles.cardGradientOverlay} />}

                <View style={styles.imageContainer}>
                    <Image source={{ uri: data.image || 'https://via.placeholder.com/400' }} style={styles.productImage} />

                    {/* PREMIUM BADGE & HEART */}
                    <View style={styles.imageOverlay}>
                        {hasRoi ? (
                            <LinearGradient
                                colors={[brand.BLUE, brand.PURPLE]}
                                start={{ x: 0, y: 0 }}
                                end={{ x: 1, y: 1 }}
                                style={styles.badge}
                            >
                                <Text style={styles.badgeEmoji}>📈</Text>
                                <Text style={styles.badgeText}>{data.roi}% ROI</Text>
                            </LinearGradient>
                        ) : null}

                        <TouchableOpacity
                            onPress={(e) => { e.stopPropagation(); toggleSave(item); }}
                            style={styles.heartBtn}
                        >
                            <Text style={{ fontSize: 20 }}>{saved ? '❤️' : '🤍'}</Text>
                        </TouchableOpacity>
                    </View>

                    {/* NEW BADGE */}
                    {!item.is_locked && (
                        <View style={styles.newBadge}>
                            <Text style={{ fontSize: 10, fontWeight: '900', color: '#FFF' }}>NEW</Text>
                        </View>
                    )}
                </View>

                <View style={[styles.cardContent, { backgroundColor: colors.card }]}>
                    {/* TITLE & CATEGORY */}
                    <View style={styles.titleRow}>
                        <View style={{ flex: 1 }}>
                            <Text style={[styles.title, { color: colors.text }]} numberOfLines={2}>
                                {data.title || 'HollowScan Product'}
                            </Text>
                        </View>
                        <LinearGradient
                            colors={[brand.BLUE + '20', brand.PURPLE + '20']}
                            start={{ x: 0, y: 0 }}
                            end={{ x: 1, y: 1 }}
                            style={styles.categoryBadge}
                        >
                            <Text style={[styles.category, { color: brand.BLUE }]}>{catName}</Text>
                        </LinearGradient>
                    </View>

                    {/* PRICE SECTION */}
                    <View style={styles.priceSection}>
                        <View style={styles.priceBlock}>
                            <Text style={[styles.priceLabel, { color: colors.textSecondary }]}>RETAIL</Text>
                            <Text style={[styles.priceValue, { color: colors.text }]}>
                                ${data.price || '0'}
                            </Text>
                        </View>

                        {hasResell && (
                            <>
                                <View style={[styles.priceDivider, { backgroundColor: colors.border }]} />
                                <View style={styles.priceBlock}>
                                    <Text style={[styles.priceLabel, { color: colors.textSecondary }]}>RESALE</Text>
                                    <Text style={[styles.priceValue, { color: brand.PURPLE, fontWeight: '900' }]}>
                                        ${data.resell}
                                    </Text>
                                </View>

                                {hasResell && data.price && (
                                    <>
                                        <View style={[styles.priceDivider, { backgroundColor: colors.border }]} />
                                        <View style={styles.priceBlock}>
                                            <Text style={[styles.priceLabel, { color: colors.textSecondary }]}>PROFIT</Text>
                                            <Text style={[styles.priceValue, { color: '#10B981', fontWeight: '900' }]}>
                                                ${Math.round(data.resell - data.price)}
                                            </Text>
                                        </View>
                                    </>
                                )}
                            </>
                        )}
                    </View>

                    {/* FOOTER */}
                    <View style={styles.footerRow}>
                        <Text style={[styles.timestamp, { color: colors.textSecondary }]}>
                            {getRelativeTime(item.created_at)}
                        </Text>
                        <Text style={{ color: brand.BLUE, fontWeight: '700', fontSize: 13 }}>
                            View details ›
                        </Text>
                    </View>
                </View>

                {/* LOCK OVERLAY */}
                {item.is_locked && (
                    <BlurView intensity={70} tint={isDarkMode ? 'dark' : 'light'} style={styles.lockOverlay}>
                        <View style={styles.lockContent}>
                            <View style={[styles.lockCircle, { backgroundColor: isDarkMode ? '#333' : '#F0F0F0' }]}>
                                <Text style={{ fontSize: 32 }}>🔒</Text>
                            </View>
                            <Text style={[styles.lockTitle, { color: colors.text }]}>Premium Deal</Text>
                            <Text style={[styles.lockDescription, { color: colors.textSecondary }]}>
                                Unlock with subscription
                            </Text>
                            <TouchableOpacity style={[styles.subscribeBtn, { backgroundColor: brand.BLUE }]}>
                                <Text style={styles.subscribeBtnText}>UPGRADE</Text>
                            </TouchableOpacity>
                        </View>
                    </BlurView>
                )}
            </TouchableOpacity>
        );
    };

    const Header = () => (
        <View style={styles.header}>
            {/* GRADIENT BACKGROUND */}
            {isDarkMode ? (
                <View style={styles.gradientBg} />
            ) : (
                <LinearGradient
                    colors={['#F8F9FE', '#F0F4FF', '#F8F9FE']}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}
                    style={styles.gradientBg}
                />
            )}

            {/* TOP BAR WITH ENHANCED STYLING */}
            <View style={styles.topBar}>
                <View style={styles.logoAndTitle}>
                    <LinearGradient
                        colors={[brand.BLUE, brand.PURPLE]}
                        start={{ x: 0, y: 0 }}
                        end={{ x: 1, y: 1 }}
                        style={[styles.logoBtn, styles.logoBtnGradient]}
                    >
                        <Text style={{ fontSize: 20 }}>⌖</Text>
                    </LinearGradient>
                    <View style={styles.titleContainer}>
                        <Text style={[styles.headerTitle, { color: colors.text }]}>Hollowscan</Text>
                        <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]}>Deal Hunter</Text>
                    </View>
                </View>

                <LinearGradient
                    colors={[brand.PURPLE + '25', brand.BLUE + '15']}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}
                    style={[styles.quotaBadge]}
                >
                    <Text style={{ fontSize: 12, marginRight: 6 }}>⚡</Text>
                    <Text style={[styles.quotaText, { color: brand.PURPLE }]}>{quota.limit - quota.used}/{quota.limit}</Text>
                </LinearGradient>
            </View>

            {/* ENHANCED SEARCH */}
            <LinearGradient
                colors={isDarkMode ? ['#1C1C1E', '#2A2A2E'] : ['#FFFFFF', '#F5F7FF']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={[styles.searchContainer, { borderColor: colors.border }]}
            >
                <Text style={{ fontSize: 16, color: colors.textSecondary, marginRight: 10 }}>🔍</Text>
                <TextInput
                    placeholder="Search products..."
                    placeholderTextColor={colors.textSecondary}
                    style={[styles.searchInput, { color: colors.text }]}
                    value={searchQuery}
                    onChangeText={setSearchQuery}
                />
            </LinearGradient>

            {/* REGION TABS WITH ENHANCED DESIGN */}
            <View style={styles.regionSelectorContainer}>
                <Text style={[styles.sectionLabel, { color: colors.textSecondary }]}>REGIONS</Text>
                <View style={styles.regionSelector}>
                    {regions.map(r => (
                        <TouchableOpacity
                            key={r.id}
                            onPress={() => setSelectedRegion(r.id)}
                            activeOpacity={0.8}
                        >
                            {selectedRegion === r.id ? (
                                <LinearGradient
                                    colors={[brand.BLUE, brand.PURPLE]}
                                    start={{ x: 0, y: 0 }}
                                    end={{ x: 1, y: 1 }}
                                    style={styles.regionBtnActive}
                                >
                                    <Text style={{ fontSize: 28, marginBottom: 4 }}>{r.flag}</Text>
                                    <Text style={[styles.regionBtnLabel, { color: '#FFF', fontWeight: '900' }]}>{r.label}</Text>
                                </LinearGradient>
                            ) : (
                                <View style={[styles.regionBtn, { backgroundColor: colors.card, borderColor: colors.border }]}>
                                    <Text style={{ fontSize: 28, marginBottom: 4 }}>{r.flag}</Text>
                                    <Text style={[styles.regionBtnLabel, { color: colors.textSecondary }]}>{r.label}</Text>
                                </View>
                            )}
                        </TouchableOpacity>
                    ))}
                </View>
            </View>

            {/* CATEGORY SELECTOR ENHANCED */}
            <TouchableOpacity
                onPress={() => setFilterVisible(true)}
                activeOpacity={0.75}
                style={{ marginBottom: 5 }}
            >
                <LinearGradient
                    colors={[colors.card, isDarkMode ? '#1C1C1E' : '#F5F7FF']}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                    style={[styles.catSelector, { borderColor: colors.border, borderWidth: 1 }]}
                >
                    <View style={{ flex: 1 }}>
                        <Text style={[styles.sectionLabel, { color: colors.textSecondary, marginBottom: 4 }]}>CATEGORY</Text>
                        <Text style={[styles.catSelectorText, { color: colors.text }]}>
                            {selectedCategories.includes('ALL')
                                ? '📁 All Categories'
                                : selectedCategories.length === 1
                                ? `📍 ${selectedCategories[0]}`
                                : `📍 ${selectedCategories.length} Selected`}
                        </Text>
                    </View>
                    <Text style={{ fontSize: 16, color: brand.PURPLE }}>›</Text>
                </LinearGradient>
            </TouchableOpacity>
        </View>
    );

    return (
        <SafeAreaView edges={['top']} style={[styles.container, { backgroundColor: colors.bg }]}>
            <StatusBar barStyle={isDarkMode ? 'light-content' : 'dark-content'} />

            <FlatList
                data={alerts}
                keyExtractor={item => item?.id?.toString() || Math.random().toString()}
                renderItem={renderProductCard}
                contentContainerStyle={styles.feedScroll}
                showsVerticalScrollIndicator={false}
                ListHeaderComponent={<Header />}
                onRefresh={onRefresh}
                refreshing={isRefreshing}
                onEndReached={handleLoadMore}
                onEndReachedThreshold={0.5}
                ListFooterComponent={isLoadingMore ? <ActivityIndicator color={brand.BLUE} style={{ marginVertical: 20 }} /> : null}
                ListEmptyComponent={!isLoading ? (
                    <View style={styles.emptyContainer}>
                        <Text style={{ color: colors.textSecondary, fontSize: 16, textAlign: 'center' }}>
                            No live alerts found for this region.{'\n'}Try pulling to refresh.
                        </Text>
                    </View>
                ) : null}
            />

            {/* ENHANCED MODAL - MULTI-SELECT */}
            <Modal visible={isFilterVisible} animationType="fade" transparent={true}>
                <BlurView intensity={90} style={styles.modalOverlay}>
                    <View style={styles.modalCenter}>
                        <View style={[styles.modalContent, { backgroundColor: colors.card }]}>
                            {/* MODAL HEADER */}
                            <View style={styles.modalHeader}>
                                <Text style={[styles.modalTitle, { color: colors.text }]}>Choose Categories</Text>
                                <TouchableOpacity
                                    onPress={() => setFilterVisible(false)}
                                    style={styles.closeBtn}
                                >
                                    <Text style={{ fontSize: 20, color: colors.textSecondary }}>✕</Text>
                                </TouchableOpacity>
                            </View>

                            <View style={[styles.modalDivider, { backgroundColor: colors.border }]} />

                            {/* CATEGORY LIST */}
                            <ScrollView style={styles.modalScroll} showsVerticalScrollIndicator={false}>
                                {/* All Categories Option */}
                                <TouchableOpacity
                                    onPress={() => {
                                        if (selectedCategories.includes('ALL')) {
                                            // If ALL is selected, just deselect it
                                            setSelectedCategories([]);
                                        } else {
                                            // Selecting ALL deselects all others
                                            setSelectedCategories(['ALL']);
                                        }
                                    }}
                                    style={[
                                        styles.categoryOption,
                                        selectedCategories.includes('ALL') && styles.categoryOptionActive,
                                        selectedCategories.includes('ALL') && { backgroundColor: brand.BLUE + '15' }
                                    ]}
                                >
                                    <Text style={{ fontSize: 16, marginRight: 10 }}>📁</Text>
                                    <View style={{ flex: 1 }}>
                                        <Text style={[styles.categoryOptionText, { color: colors.text }]}>
                                            All Categories
                                        </Text>
                                        <Text style={[styles.categoryOptionSub, { color: colors.textSecondary }]}>
                                            Show all available deals
                                        </Text>
                                    </View>
                                    <View
                                        style={[
                                            styles.checkbox,
                                            selectedCategories.includes('ALL') && {
                                                backgroundColor: brand.BLUE,
                                                borderColor: brand.BLUE
                                            }
                                        ]}
                                    >
                                        {selectedCategories.includes('ALL') && (
                                            <Text style={{ color: '#FFF', fontSize: 12, fontWeight: '900' }}>✓</Text>
                                        )}
                                    </View>
                                </TouchableOpacity>

                                {/* Individual Categories */}
                                {currentSubcategories.filter(s => s !== 'ALL').map((sub) => (
                                    <TouchableOpacity
                                        key={sub}
                                        onPress={() => {
                                            setSelectedCategories(prev => {
                                                // If selecting a specific category and ALL is selected, remove ALL
                                                if (prev.includes('ALL')) {
                                                    return [sub];
                                                }
                                                // If category is already selected, remove it
                                                if (prev.includes(sub)) {
                                                    const updated = prev.filter(c => c !== sub);
                                                    // If no categories selected, select ALL
                                                    return updated.length === 0 ? ['ALL'] : updated;
                                                }
                                                // Otherwise add it
                                                return [...prev, sub];
                                            });
                                        }}
                                        style={[
                                            styles.categoryOption,
                                            selectedCategories.includes(sub) && styles.categoryOptionActive,
                                            selectedCategories.includes(sub) && { backgroundColor: brand.PURPLE + '15' }
                                        ]}
                                    >
                                        <Text style={{ fontSize: 16, marginRight: 10 }}>📍</Text>
                                        <View style={{ flex: 1 }}>
                                            <Text style={[styles.categoryOptionText, { color: colors.text }]}>
                                                {sub}
                                            </Text>
                                            <Text style={[styles.categoryOptionSub, { color: colors.textSecondary }]}>
                                                {selectedRegion} • Category
                                            </Text>
                                        </View>
                                        <View
                                            style={[
                                                styles.checkbox,
                                                selectedCategories.includes(sub) && {
                                                    backgroundColor: brand.PURPLE,
                                                    borderColor: brand.PURPLE
                                                }
                                            ]}
                                        >
                                            {selectedCategories.includes(sub) && (
                                                <Text style={{ color: '#FFF', fontSize: 12, fontWeight: '900' }}>✓</Text>
                                            )}
                                        </View>
                                    </TouchableOpacity>
                                ))}
                            </ScrollView>

                            {/* MODAL FOOTER WITH ACTION BUTTONS */}
                            <View style={[styles.modalFooter, { borderTopColor: colors.border }]}>
                                <TouchableOpacity
                                    onPress={() => setFilterVisible(false)}
                                    style={[styles.modalBtn, { backgroundColor: colors.tabInactive, flex: 1 }]}
                                >
                                    <Text style={[styles.modalBtnText, { color: colors.text }]}>Cancel</Text>
                                </TouchableOpacity>
                                <TouchableOpacity
                                    onPress={() => setFilterVisible(false)}
                                    style={[styles.modalBtn, { backgroundColor: brand.BLUE, flex: 1, marginLeft: 12 }]}
                                >
                                    <Text style={[styles.modalBtnText, { color: '#FFF', fontWeight: '900' }]}>Apply</Text>
                                </TouchableOpacity>
                            </View>
                        </View>
                    </View>
                </BlurView>
            </Modal>

            {isLoading && (
                <View style={styles.loadingOverlay}>
                    <ActivityIndicator size="large" color={brand.BLUE} />
                </View>
            )}
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1 },
    
    // HEADER STYLES
    header: { paddingHorizontal: 20, paddingTop: 10, paddingBottom: 20, position: 'relative' },
    gradientBg: {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: 320,
        zIndex: -1,
        backgroundColor: 'rgba(45, 130, 255, 0.02)'
    },

    topBar: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
    logoAndTitle: { flexDirection: 'row', alignItems: 'center', flex: 1 },
    logoBtn: { width: 50, height: 50, borderRadius: 14, justifyContent: 'center', alignItems: 'center', marginRight: 12 },
    logoBtnGradient: { shadowColor: '#2D82FF', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 8, elevation: 5 },
    titleContainer: { justifyContent: 'center' },
    headerTitle: { fontSize: 26, fontWeight: '900', letterSpacing: -0.5 },
    headerSubtitle: { fontSize: 11, fontWeight: '600', letterSpacing: 0.5, marginTop: 2 },

    quotaBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 12,
        paddingVertical: 10,
        borderRadius: 20,
        shadowColor: '#9B4DFF',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.15,
        shadowRadius: 6,
        elevation: 3
    },
    quotaText: { fontWeight: '800', fontSize: 13 },

    searchContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 16,
        height: 50,
        borderRadius: 16,
        borderWidth: 1,
        marginBottom: 20,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 6,
        elevation: 2
    },
    searchInput: { flex: 1, fontSize: 15, fontWeight: '600' },

    regionSelectorContainer: { marginBottom: 20 },
    sectionLabel: { fontSize: 10, fontWeight: '900', letterSpacing: 1, marginBottom: 10 },
    regionSelector: { flexDirection: 'row', justifyContent: 'space-between', gap: 10 },
    regionBtn: {
        flex: 1,
        height: 90,
        borderRadius: 18,
        borderWidth: 1,
        justifyContent: 'center',
        alignItems: 'center',
        aspectRatio: 1,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 4,
        elevation: 1
    },
    regionBtnActive: {
        flex: 1,
        height: 90,
        borderRadius: 18,
        justifyContent: 'center',
        alignItems: 'center',
        aspectRatio: 1,
        shadowColor: '#2D82FF',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
        elevation: 5
    },
    regionBtnLabel: { fontSize: 12, fontWeight: '800', marginTop: 6 },

    catSelector: {
        flexDirection: 'row',
        alignItems: 'center',
        height: 70,
        borderRadius: 16,
        paddingHorizontal: 16,
        paddingVertical: 12,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 4,
        elevation: 1
    },
    catSelectorText: { fontSize: 15, fontWeight: '800' },

    // FEED STYLES
    feedScroll: { paddingBottom: 30 },

    card: {
        marginHorizontal: 16,
        borderRadius: 24,
        marginBottom: 20,
        overflow: 'hidden',
        borderWidth: 1,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.12,
        shadowRadius: 16,
        elevation: 8,
        backgroundColor: '#FFFFFF'
    },
    cardGradientOverlay: {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.02)',
        zIndex: 1,
        pointerEvents: 'none'
    },

    imageContainer: { width: '100%', height: 220, backgroundColor: '#F5F5F5', position: 'relative' },
    productImage: { width: '100%', height: '100%', resizeMode: 'contain' },
    imageOverlay: {
        position: 'absolute',
        top: 12,
        left: 12,
        right: 12,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        zIndex: 2
    },

    badge: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderRadius: 12,
        shadowColor: '#2D82FF',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
        elevation: 4
    },
    badgeEmoji: { fontSize: 14, marginRight: 4 },
    badgeText: { color: '#FFF', fontWeight: '900', fontSize: 12 },

    newBadge: {
        position: 'absolute',
        bottom: 12,
        left: 12,
        backgroundColor: '#10B981',
        paddingHorizontal: 10,
        paddingVertical: 6,
        borderRadius: 8,
        shadowColor: '#10B981',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.3,
        shadowRadius: 4,
        elevation: 2,
        zIndex: 2
    },

    heartBtn: {
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        width: 44,
        height: 44,
        borderRadius: 22,
        justifyContent: 'center',
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.2,
        shadowRadius: 8,
        elevation: 4
    },

    cardContent: {
        padding: 20,
        backgroundColor: '#FFFFFF'
    },
    titleRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 14,
        gap: 10
    },
    title: { fontSize: 16, fontWeight: '800', flex: 1, lineHeight: 22 },
    categoryBadge: {
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderRadius: 10,
        justifyContent: 'center',
        alignItems: 'center'
    },
    category: { fontSize: 11, fontWeight: '900', letterSpacing: 0.5 },

    priceSection: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 16,
        backgroundColor: 'rgba(45, 130, 255, 0.03)',
        borderRadius: 12,
        paddingHorizontal: 12,
        paddingVertical: 10
    },
    priceBlock: { justifyContent: 'center', flex: 1 },
    priceLabel: { fontSize: 9, fontWeight: '700', letterSpacing: 0.5, marginBottom: 4, textTransform: 'uppercase' },
    priceValue: { fontSize: 18, fontWeight: '900' },
    priceDivider: { width: 1, height: 35, marginHorizontal: 14, opacity: 0.15 },

    footerRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: 10,
        paddingTop: 12,
        borderTopWidth: 1,
        borderTopColor: 'rgba(0, 0, 0, 0.06)'
    },
    timestamp: { fontSize: 12, fontWeight: '500' },

    lockOverlay: {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        justifyContent: 'center',
        alignItems: 'center',
        borderRadius: 24
    },
    lockContent: { alignItems: 'center', padding: 25 },
    lockCircle: { width: 80, height: 80, borderRadius: 40, justifyContent: 'center', alignItems: 'center', marginBottom: 16 },
    lockTitle: { fontSize: 24, fontWeight: '900', marginBottom: 8 },
    lockDescription: { fontSize: 13, marginBottom: 20, textAlign: 'center' },
    subscribeBtn: {
        paddingHorizontal: 40,
        paddingVertical: 14,
        borderRadius: 12,
        shadowColor: '#2D82FF',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
        elevation: 4
    },
    subscribeBtnText: { color: '#FFF', fontWeight: '900', fontSize: 14, letterSpacing: 0.5 },

    // MODAL STYLES
    modalOverlay: {
        flex: 1,
        justifyContent: 'flex-end',
        backgroundColor: 'rgba(0, 0, 0, 0.5)'
    },
    modalCenter: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        paddingHorizontal: 16
    },
    modalContent: {
        borderRadius: 28,
        maxHeight: '70%',
        width: '100%',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 20 },
        shadowOpacity: 0.25,
        shadowRadius: 20,
        elevation: 10,
        overflow: 'hidden'
    },
    modalHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 20,
        paddingTop: 22,
        paddingBottom: 16
    },
    modalTitle: { fontSize: 22, fontWeight: '900', flex: 1 },
    closeBtn: { width: 36, height: 36, justifyContent: 'center', alignItems: 'center' },
    modalDivider: { height: 1, marginHorizontal: 20, opacity: 0.1 },
    modalScroll: { maxHeight: 400 },

    categoryOption: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 16,
        paddingVertical: 16,
        borderBottomWidth: 1,
        borderBottomColor: 'rgba(0, 0, 0, 0.05)'
    },
    categoryOptionActive: {
        borderLeftWidth: 4,
        borderLeftColor: 'rgba(45, 130, 255, 0.5)',
        paddingLeft: 12
    },
    categoryOptionText: { fontSize: 15, fontWeight: '700', marginBottom: 4 },
    categoryOptionSub: { fontSize: 12, fontWeight: '500' },

    checkbox: {
        width: 24,
        height: 24,
        borderRadius: 6,
        borderWidth: 2,
        borderColor: '#CCCCCC',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: 'transparent',
        marginLeft: 12
    },

    modalFooter: {
        borderTopWidth: 1,
        paddingHorizontal: 16,
        paddingVertical: 14,
        flexDirection: 'row',
        gap: 10
    },
    modalBtn: {
        height: 48,
        borderRadius: 12,
        justifyContent: 'center',
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.08,
        shadowRadius: 4,
        elevation: 2
    },
    modalBtnText: { fontWeight: '800', fontSize: 15, letterSpacing: 0.5 },
    modalCancelBtn: {
        flex: 1,
        height: 50,
        borderRadius: 12,
        justifyContent: 'center',
        alignItems: 'center'
    },
    modalCancelText: { fontWeight: '800', fontSize: 15, letterSpacing: 0.5 },

    // OTHER
    emptyContainer: { flex: 1, marginTop: 100, paddingHorizontal: 40, justifyContent: 'center', alignItems: 'center' },
    loadingOverlay: {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.9)'
    }
});

export default HomeScreen;
