import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

export default async function V2RedirectPage() {
  const cookieStore = await cookies();
  const savedLocale = cookieStore.get('NEXT_LOCALE')?.value;
  const locale = savedLocale === 'en' ? 'en' : 'zh';

  redirect(`/${locale}/v2`);
}
