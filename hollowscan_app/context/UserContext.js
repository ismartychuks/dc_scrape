import React, { createContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const UserContext = createContext();

export const UserProvider = ({ children }) => {
    const [user, setUser] = useState({
        id: '8923304e-657e-4e7e-800a-94e7248ecf7f', // Default/demo user from Supabase
        isPremium: false,
        subscriptionEnd: null,
    });

    const [dailyViews, setDailyViews] = useState({
        date: new Date().toDateString(),
        products: [],
    });

    const FREE_PRODUCT_LIMIT = 4;

    // Load user data on mount
    useEffect(() => {
        loadUserData();
        loadDailyViews();
    }, []);

    const loadUserData = async () => {
        try {
            const stored = await AsyncStorage.getItem('user_data');
            if (stored) {
                setUser(JSON.parse(stored));
            }
        } catch (error) {
            console.error('[USER] Error loading user data:', error);
        }
    };

    const loadDailyViews = async () => {
        try {
            const stored = await AsyncStorage.getItem('daily_views');
            if (stored) {
                const data = JSON.parse(stored);
                // Check if date needs reset (midnight reset)
                if (data.date !== new Date().toDateString()) {
                    // Reset for new day
                    const newData = {
                        date: new Date().toDateString(),
                        products: [],
                    };
                    setDailyViews(newData);
                    await AsyncStorage.setItem('daily_views', JSON.stringify(newData));
                } else {
                    setDailyViews(data);
                }
            } else {
                // First time - initialize
                const newData = {
                    date: new Date().toDateString(),
                    products: [],
                };
                setDailyViews(newData);
                await AsyncStorage.setItem('daily_views', JSON.stringify(newData));
            }
        } catch (error) {
            console.error('[USER] Error loading daily views:', error);
        }
    };

    const trackProductView = async (productId) => {
        try {
            // Check if premium - bypass limit
            if (user.isPremium) {
                console.log('[LIMIT] Premium user - unlimited views');
                return { allowed: true, remaining: Infinity };
            }

            // Get current daily views
            const stored = await AsyncStorage.getItem('daily_views');
            let current = stored ? JSON.parse(stored) : { date: new Date().toDateString(), products: [] };

            // Check if date changed (midnight reset)
            if (current.date !== new Date().toDateString()) {
                current = { date: new Date().toDateString(), products: [] };
            }

            // Check if product already viewed today
            if (current.products.includes(productId)) {
                console.log('[LIMIT] Product already viewed today');
                const remaining = FREE_PRODUCT_LIMIT - current.products.length;
                return { allowed: true, remaining };
            }

            // Check if limit reached
            if (current.products.length >= FREE_PRODUCT_LIMIT) {
                console.log('[LIMIT] Daily limit reached (', current.products.length, '/', FREE_PRODUCT_LIMIT, ')');
                return { allowed: false, remaining: 0 };
            }

            // Add product to viewed list
            current.products.push(productId);
            setDailyViews(current);
            await AsyncStorage.setItem('daily_views', JSON.stringify(current));

            const remaining = FREE_PRODUCT_LIMIT - current.products.length;
            console.log('[LIMIT] View tracked. Remaining:', remaining);
            return { allowed: true, remaining };
        } catch (error) {
            console.error('[LIMIT] Error tracking view:', error);
            return { allowed: true, remaining: -1 };
        }
    };

    const getRemainingViews = () => {
        return Math.max(0, FREE_PRODUCT_LIMIT - dailyViews.products.length);
    };

    const updateUser = async (userData) => {
        try {
            setUser(userData);
            await AsyncStorage.setItem('user_data', JSON.stringify(userData));
        } catch (error) {
            console.error('[USER] Error updating user:', error);
        }
    };

    const resetDailyViews = async () => {
        const newData = {
            date: new Date().toDateString(),
            products: [],
        };
        setDailyViews(newData);
        await AsyncStorage.setItem('daily_views', JSON.stringify(newData));
    };

    const isPremium = user?.isPremium || false;

    return (
        <UserContext.Provider
            value={{
                user,
                dailyViews,
                trackProductView,
                getRemainingViews,
                updateUser,
                resetDailyViews,
                isPremium,
            }}
        >
            {children}
        </UserContext.Provider>
    );
};
