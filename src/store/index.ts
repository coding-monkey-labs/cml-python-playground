import { configureStore } from '@reduxjs/toolkit';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';
import dashboardReducer from './dashboardSlice';
import themeReducer from './themeSlice';
import { RootState } from '../types';

export const store = configureStore({
  reducer: {
    dashboard: dashboardReducer,
    theme: themeReducer,
  },
});

export type AppDispatch = typeof store.dispatch;
export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
