import React, { Dispatch, SetStateAction } from 'react';

export const handleAuthorizationError = (
    error: unknown,
    setStatusError: Dispatch<SetStateAction<string>>,
    setShowLoginModal: Dispatch<SetStateAction<boolean>>,
    setRedirectAfterLogin: Dispatch<SetStateAction<boolean>>
) => {
    if (error instanceof Error) {
        if (error.message.includes('Unauthorized')) {
            setShowLoginModal(true);
            setRedirectAfterLogin(true);
        } else {
            setStatusError('Error: ' + error.message);
        }
    } else {
        setStatusError('An unknown error occurred');
    }
};
