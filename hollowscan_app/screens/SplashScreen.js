import React, { useEffect, useRef } from 'react';
import { StyleSheet, View, Text, Image, Animated } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import Constants from '../Constants';

const SplashScreen = ({ onComplete }) => {
    const brand = Constants.BRAND;
    
    // Animation refs
    const scaleAnim = useRef(new Animated.Value(0.3)).current;
    const opacityAnim = useRef(new Animated.Value(0)).current;
    const slideAnim = useRef(new Animated.Value(30)).current;

    useEffect(() => {
        // Logo scale animation
        Animated.sequence([
            Animated.parallel([
                Animated.timing(scaleAnim, {
                    toValue: 1,
                    duration: 600,
                    useNativeDriver: true,
                }),
                Animated.timing(opacityAnim, {
                    toValue: 1,
                    duration: 600,
                    useNativeDriver: true,
                }),
            ]),
            // Text slide up animation
            Animated.timing(slideAnim, {
                toValue: 0,
                duration: 500,
                useNativeDriver: true,
            }),
        ]).start(() => {
            // Wait a bit then call onComplete
            setTimeout(onComplete, 800);
        });
    }, [scaleAnim, opacityAnim, slideAnim, onComplete]);

    return (
        <LinearGradient
            colors={[brand.DARK_BG, brand.BLUE + '20']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.container}
        >
            <SafeAreaView style={styles.safeArea}>
                {/* LOGO WITH BOUNCE ANIMATION */}
                <Animated.View
                    style={[
                        styles.logoContainer,
                        {
                            transform: [
                                { scale: scaleAnim },
                                {
                                    translateY: slideAnim.interpolate({
                                        inputRange: [0, 30],
                                        outputRange: [0, 30],
                                    }),
                                },
                            ],
                            opacity: opacityAnim,
                        },
                    ]}
                >
                    <LinearGradient
                        colors={[brand.BLUE, brand.PURPLE]}
                        start={{ x: 0, y: 0 }}
                        end={{ x: 1, y: 1 }}
                        style={styles.logoBg}
                    >
                        <Text style={styles.logoIcon}>⌖</Text>
                    </LinearGradient>
                </Animated.View>

                {/* TEXT SECTION */}
                <Animated.View
                    style={[
                        styles.textContainer,
                        {
                            opacity: opacityAnim,
                            transform: [
                                {
                                    translateY: slideAnim,
                                },
                            ],
                        },
                    ]}
                >
                    <Text style={styles.title}>Hollowscan</Text>
                    <Text style={styles.subtitle}>Deal Hunter</Text>
                    <Text style={styles.description}>Finding profit opportunities</Text>
                </Animated.View>

                {/* LOADING INDICATOR */}
                <View style={styles.loaderContainer}>
                    <View style={[styles.loaderDot, { backgroundColor: brand.BLUE }]} />
                    <View style={[styles.loaderDot, { backgroundColor: brand.PURPLE, marginHorizontal: 8 }]} />
                    <View style={[styles.loaderDot, { backgroundColor: brand.BLUE }]} />
                </View>
            </SafeAreaView>
        </LinearGradient>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    safeArea: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    logoContainer: {
        marginBottom: 40,
    },
    logoBg: {
        width: 100,
        height: 100,
        borderRadius: 28,
        justifyContent: 'center',
        alignItems: 'center',
        shadowColor: '#2D82FF',
        shadowOffset: { width: 0, height: 12 },
        shadowOpacity: 0.4,
        shadowRadius: 20,
        elevation: 10,
    },
    logoIcon: {
        fontSize: 50,
        color: '#FFF',
    },
    textContainer: {
        alignItems: 'center',
        marginBottom: 60,
    },
    title: {
        fontSize: 36,
        fontWeight: '900',
        color: '#FFF',
        marginBottom: 4,
        letterSpacing: -0.5,
    },
    subtitle: {
        fontSize: 16,
        fontWeight: '700',
        color: '#9B4DFF',
        marginBottom: 12,
        letterSpacing: 0.5,
    },
    description: {
        fontSize: 13,
        fontWeight: '600',
        color: 'rgba(255, 255, 255, 0.6)',
        letterSpacing: 0.3,
    },
    loaderContainer: {
        position: 'absolute',
        bottom: 60,
        flexDirection: 'row',
        justifyContent: 'center',
        alignItems: 'center',
    },
    loaderDot: {
        width: 10,
        height: 10,
        borderRadius: 5,
    },
});

export default SplashScreen;
