import { db } from './firebase';
import { collection, addDoc, serverTimestamp, query, orderBy, getDocs, updateDoc, doc } from 'firebase/firestore';

export interface Order {
  id?: string;
  customerName: string;
  customerPhone: string;
  address: string;
  items: {
    productId: string;
    productName: string;
    quantity: number;
    price: number;
  }[];
  total: number;
  status: 'PENDING' | 'SHIPPED' | 'COMPLETED' | 'CANCELLED';
  createdAt?: any;
}

const ORDERS_COLLECTION = 'orders';

export const createOrder = async (order: Omit<Order, 'id' | 'status' | 'createdAt'>) => {
  try {
    const docRef = await addDoc(collection(db, ORDERS_COLLECTION), {
      ...order,
      status: 'PENDING',
      createdAt: serverTimestamp(),
    });
    return docRef.id;
  } catch (error) {
    console.error('Error creating order:', error);
    throw error;
  }
};

export const getOrders = async () => {
  try {
    const q = query(collection(db, ORDERS_COLLECTION), orderBy('createdAt', 'desc'));
    const querySnapshot = await getDocs(q);
    return querySnapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    })) as Order[];
  } catch (error) {
    console.error('Error fetching orders:', error);
    throw error;
  }
};

export const updateOrderStatus = async (orderId: string, status: Order['status']) => {
  try {
    const orderRef = doc(db, ORDERS_COLLECTION, orderId);
    await updateDoc(orderRef, { status });
  } catch (error) {
    console.error('Error updating order status:', error);
    throw error;
  }
};
