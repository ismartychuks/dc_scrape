import React from 'react';
import {
    StyleSheet,
    View,
    Text,
    Image,
    ScrollView,
    TouchableOpacity,
    Dimensions,
    Linking
} from 'react-native';

const { width } = Dimensions.get('window');

/**
 * SmartyMetrics Professional Product Detail Screen
 */
const ProductDetailScreen = ({ route, isDarkMode }) => {
    // Mock data for structure - in real app this comes from route.params
    const product = {
        title: "Sony PlayStation 5 Console",
        price: 499.00,
        profit: "+$120.00",
        images: ["https://via.placeholder.com/800"],
        buyLinks: [
            { store: "Sony Store", url: "https://sony.com" },
            { store: "Target", url: "https://target.com" }
        ],
        researchLinks: [
            { label: "Amazon / Keepa", url: "https://amazon.com" },
            { label: "eBay Sold", url: "https://ebay.com" }
        ]
    };

    const colors = isDarkMode ? {
        bg: '#121212',
        card: '#1E1E1E',
        text: '#FFFFFF',
        textSecondary: '#A0A0A0',
        accent: '#00D09C',
        buttonBg: '#333333',
        border: '#2C2C2E'
    } : {
        bg: '#FFFFFF',
        card: '#F5F5F7',
        text: '#1D1D1F',
        textSecondary: '#6E6E73',
        accent: '#007AFF',
        buttonBg: '#F2F2F7',
        border: '#E5E5E7'
    };

    const openUrl = (url) => Linking.openURL(url);

    return (
        <ScrollView style={[styles.container, { backgroundColor: colors.bg }]}>
            {/* IMAGE GALLERY */}
            <ScrollView horizontal pagingEnabled showsHorizontalScrollIndicator={false} style={styles.gallery}>
                {product.images.map((img, index) => (
                    <Image key={index} source={{ uri: img }} style={styles.largeImage} />
                ))}
            </ScrollView>

            <View style={styles.content}>
                <Text style={[styles.title, { color: colors.text }]}>{product.title}</Text>
                <View style={styles.priceRow}>
                    <Text style={[styles.price, { color: colors.text }]}>${product.price.toFixed(2)}</Text>
                    <Text style={[styles.profit, { color: colors.accent }]}>{product.profit}</Text>
                </View>

                {/* BUYING OPTIONS (MULTIPLE LINKS) */}
                <View style={styles.section}>
                    <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>BUYING OPTIONS</Text>
                    {product.buyLinks.map((link, index) => (
                        <TouchableOpacity
                            key={index}
                            style={[styles.buyBtn, { backgroundColor: colors.accent }]}
                            onPress={() => openUrl(link.url)}
                        >
                            <Text style={styles.buyBtnText}>🛒 BUY AT {link.store.toUpperCase()}</Text>
                        </TouchableOpacity>
                    ))}
                </View>

                {/* RESEARCH LINKS */}
                <View style={styles.section}>
                    <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>RESEARCH & ANALYTICS</Text>
                    <View style={styles.researchGrid}>
                        {product.researchLinks.map((link, index) => (
                            <TouchableOpacity
                                key={index}
                                style={[styles.researchBtn, { backgroundColor: colors.buttonBg }]}
                                onPress={() => openUrl(link.url)}
                            >
                                <Text style={[styles.researchBtnText, { color: colors.text }]}>{link.label}</Text>
                            </TouchableOpacity>
                        ))}
                    </View>
                </View>
            </View>
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1 },
    gallery: { height: width, width: width },
    largeImage: { width: width, height: width, resizeMode: 'cover' },
    content: { padding: 20 },
    title: { fontSize: 22, fontWeight: '800', marginBottom: 10 },
    priceRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 25 },
    price: { fontSize: 24, fontWeight: '700', marginRight: 15 },
    profit: { fontSize: 18, fontWeight: '800' },
    section: { marginBottom: 30 },
    sectionTitle: { fontSize: 13, fontWeight: '700', letterSpacing: 1, marginBottom: 15 },
    buyBtn: {
        height: 56,
        borderRadius: 16,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 12,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.1,
        shadowRadius: 8,
        elevation: 4
    },
    buyBtnText: { color: '#000', fontSize: 16, fontWeight: '900' },
    researchGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
    researchBtn: {
        width: '48%',
        height: 50,
        borderRadius: 12,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 12
    },
    researchBtnText: { fontSize: 14, fontWeight: '700' }
});

export default ProductDetailScreen;
