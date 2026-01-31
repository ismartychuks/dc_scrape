import React, { useContext } from 'react';
import { StyleSheet, View, Text, FlatList, TouchableOpacity, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { SavedContext } from '../context/SavedContext';
import Constants from '../Constants';

const SavedScreen = ({ navigation }) => {
    const { savedProducts } = useContext(SavedContext);
    const brand = Constants.BRAND;

    const renderItem = ({ item }) => {
        const data = item.product_data || {};
        return (
            <TouchableOpacity
                style={styles.card}
                onPress={() => navigation.navigate('ProductDetail', { product: item })}
            >
                <Image source={{ uri: data.image || 'https://via.placeholder.com/150' }} style={styles.image} />
                <View style={styles.cardContent}>
                    <Text style={styles.title} numberOfLines={2}>{data.title}</Text>
                    <View style={styles.priceRow}>
                        <Text style={styles.price}>${data.price}</Text>
                        {data.roi && <Text style={styles.roi}>+{data.roi}% ROI</Text>}
                    </View>
                </View>
            </TouchableOpacity>
        );
    };

    return (
        <SafeAreaView style={styles.container} edges={['top']}>
            <View style={styles.header}>
                <Text style={styles.headerTitle}>Saved Deals</Text>
                <Text style={styles.stats}>{savedProducts.length} saved</Text>
            </View>

            {savedProducts.length === 0 ? (
                <View style={styles.emptyState}>
                    <Text style={styles.emptyIcon}>❤️</Text>
                    <Text style={styles.emptyTitle}>No Saved Deals Yet</Text>
                    <Text style={styles.emptySubtitle}>Tap the heart on any product to save it for later!</Text>
                    <TouchableOpacity
                        style={[styles.browseBtn, { borderColor: brand.BLUE }]}
                        onPress={() => navigation.navigate('Home')}
                    >
                        <Text style={[styles.browseText, { color: brand.BLUE }]}>Browse Deals</Text>
                    </TouchableOpacity>
                </View>
            ) : (
                <FlatList
                    data={savedProducts}
                    renderItem={renderItem}
                    keyExtractor={item => item.id}
                    contentContainerStyle={styles.list}
                />
            )}
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#FAF9F6' },
    header: { padding: 20, borderBottomWidth: 1, borderBottomColor: '#E5E7EB', backgroundColor: '#FFF' },
    headerTitle: { fontSize: 24, fontWeight: '800', color: '#1F2937' },
    stats: { color: '#6B7280', marginTop: 5 },

    list: { padding: 20 },
    card: { flexDirection: 'row', backgroundColor: '#FFF', borderRadius: 16, marginBottom: 15, padding: 10, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 5 },
    image: { width: 80, height: 80, borderRadius: 12 },
    cardContent: { flex: 1, marginLeft: 15, justifyContent: 'center' },
    title: { fontWeight: '700', fontSize: 15, marginBottom: 8, color: '#1F2937' },
    priceRow: { flexDirection: 'row', alignItems: 'center' },
    price: { fontSize: 16, fontWeight: '800', marginRight: 10 },
    roi: { color: '#10B981', fontWeight: '700', fontSize: 13 },

    emptyState: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
    emptyIcon: { fontSize: 60, marginBottom: 20, opacity: 0.2 },
    emptyTitle: { fontSize: 20, fontWeight: '800', color: '#374151', marginBottom: 10 },
    emptySubtitle: { textAlign: 'center', color: '#6B7280', lineHeight: 22, marginBottom: 30 },
    browseBtn: { paddingHorizontal: 30, paddingVertical: 15, borderRadius: 12, borderWidth: 1 },
    browseText: { fontWeight: '700', fontSize: 16 }
});

export default SavedScreen;
