import { auth, googleProvider, db } from './firebase';
import { signInWithPopup, signOut, onAuthStateChanged, User } from 'firebase/auth';
import { doc, getDoc } from 'firebase/firestore';

// Check if user is admin by looking up their UID in admin_users collection
export const isAdminUser = async (user: User | null): Promise<boolean> => {
  if (!user) return false;

  try {
    const adminDoc = await getDoc(doc(db, 'admin_users', user.uid));
    return adminDoc.exists();
  } catch (error) {
    console.error('Error checking admin status:', error);
    return false;
  }
};

export const loginWithGoogle = async () => {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    const user = result.user;

    // Check if user is an admin
    const isAdmin = await isAdminUser(user);

    if (!isAdmin) {
      await signOut(auth);
      throw new Error('Unauthorized account. Access restricted to administrator.');
    }

    return user;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

export const logout = async () => {
  await signOut(auth);
};

export const isUserAdmin = (user: User | null) => {
  // This is a synchronous check - for immediate UI feedback
  // For proper admin verification, use isAdminUser() instead
  return user !== null;
};

export const subscribeToAuthChanges = (callback: (user: User | null) => void) => {
  return onAuthStateChanged(auth, callback);
};
