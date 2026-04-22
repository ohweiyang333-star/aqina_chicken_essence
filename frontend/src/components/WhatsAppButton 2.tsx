import { useTranslations } from 'next-intl';
import Image from 'next/image';
import { MessageCircle } from 'lucide-react';

export default function WhatsAppButton() {
  const t = useTranslations('Index');
  const phoneNumber = "6590000000"; // Placeholder SG number
  const message = encodeURIComponent("Hi Aqina SG, I'm interested in your Ancient Chicken Essence!");

  return (
    <a 
      href={`https://wa.me/${phoneNumber}?text=${message}`}
      target="_blank"
      rel="noopener noreferrer"
      className="fixed bottom-8 right-8 z-[150] group flex items-center space-x-3 bg-[#25D366] text-white p-4 rounded-full shadow-2xl hover:scale-110 active:scale-95 transition-all duration-300"
    >
      <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-10 rounded-full transition-opacity"></div>
      <MessageCircle size={28} />
      <span className="hidden md:inline font-bold pr-2 tracking-tight">Chat with Specialist</span>
    </a>
  );
}
