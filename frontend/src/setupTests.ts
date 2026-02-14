// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Polyfill TextEncoder/TextDecoder for jsdom (needed by React Router v7)
import { TextEncoder, TextDecoder } from 'util';
Object.assign(global, { TextEncoder, TextDecoder });
