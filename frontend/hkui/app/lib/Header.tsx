// app/lib/Header.tsx

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import styles from '@/app/styles/Api.module.css';

const Header: React.FC = () => {
    const [isDropdownVisible, setIsDropdownVisible] = useState(false);
    const router = useRouter();

    const handleLogout = () => {
        localStorage.removeItem('token');
        router.push('/');
    };

    return (
        <header className={styles.header}>
            <div className={styles.logo}>HKUI</div>
            <div className={styles.userProfile} onClick={() => setIsDropdownVisible(!isDropdownVisible)}>
                <img src="/profile.png" alt="User Profile" />
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
