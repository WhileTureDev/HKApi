// app/lib/Header.tsx

'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import styles from '@/app/styles/shared.module.css';
import userIcon from './img/user-icon-2048x2048-ihoxz4vq.png'; // Import the image

const Header: React.FC = () => {
    const [isDropdownVisible, setIsDropdownVisible] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const router = useRouter();

    const handleLogout = () => {
        localStorage.removeItem('token');
        router.push('/');
    };

    const toggleDropdown = () => {
        setIsDropdownVisible(!isDropdownVisible);
    };

    const handleClickOutside = (event: MouseEvent) => {
        if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
            setIsDropdownVisible(false);
        }
    };

    useEffect(() => {
        if (isDropdownVisible) {
            document.addEventListener('click', handleClickOutside);
        } else {
            document.removeEventListener('click', handleClickOutside);
        }

        return () => {
            document.removeEventListener('click', handleClickOutside);
        };
    }, [isDropdownVisible]);

    return (
        <header className={styles.header}>
            <div className={styles.logo}>HKUI</div>
            <div className={styles.userProfile} onClick={toggleDropdown} ref={dropdownRef}>
                <img src={userIcon.src} alt="User Profile" className={styles.userIcon} /> {/* Use the imported image */}
                {isDropdownVisible && (
                    <div className={styles.dropdownMenu}>
                        <Link href="/profile">Profile</Link>
                        <Link href="/settings">User Settings</Link>
                        <button onClick={handleLogout}>Logout</button>
                    </div>
                )}
            </div>
        </header>
    );
};

export default Header;
