import React, { createContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const SavedContext = createContext();

export const SavedProvider = ({ children }) => {
    const [savedProducts, setSavedProducts] = useState([]);

    useEffect(() => {
        loadSavedProducts();
    }, []);

    const loadSavedProducts = async () => {
        try {
            const stored = await AsyncStorage.getItem('savedProducts');
            if (stored) {
                setSavedProducts(JSON.parse(stored));
            }
        } catch (e) {
            console.log("Failed to load saved products", e);
        }
    };

    const toggleSave = async (product) => {
        try {
            let newSaved;
            const exists = savedProducts.some(p => p.id === product.id);

            if (exists) {
                newSaved = savedProducts.filter(p => p.id !== product.id);
            } else {
                newSaved = [...savedProducts, product];
            }

            setSavedProducts(newSaved);
            await AsyncStorage.setItem('savedProducts', JSON.stringify(newSaved));
        } catch (e) {
            console.log("Failed to save product", e);
        }
    };

    const isSaved = (productId) => {
        return savedProducts.some(p => p.id === productId);
    };

    return (
        <SavedContext.Provider value={{ savedProducts, toggleSave, isSaved }}>
            {children}
        </SavedContext.Provider>
    );
};
