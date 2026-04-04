'use client';

import { useTranslations } from 'next-intl';
import { Star, Quote } from 'lucide-react';

export default function TestimonialsSection() {
  const t = useTranslations('Testimonials');

  const testimonials = [
    {
      role: t('customer1.role') || 'Urban Professional',
      text: t('customer1.text') || '"First sip was amazing! Absolutely no "weird taste" at all, just like a freshly brewed rich chicken soup."',
      stars: 5,
    },
    {
      role: t('customer2.role') || 'Expecting Mother',
      text: t('customer2.text') || '"Even during severe pregnancy nausea, this taste was acceptable. The Halal certification gives me peace of mind while drinking."',
      stars: 5,
    },
    {
      role: t('customer3.role') || 'Homemaker',
      text: t('customer3.text') || '"It\'s absolutely amazing for cooking noodles! So delicious that I drank up all the soup!"',
      stars: 5,
    },
  ];

  return (
    <section className="w-full py-24 px-6 sm:px-12 bg-ivory" id="testimonials">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16 space-y-4">
          <span className="text-secondary font-bold tracking-widest text-sm uppercase">
            {t('subtitle') || 'Customer Stories'}
          </span>
          <h2 className="text-4xl md:text-5xl font-bold text-charcoal">
            {t('title') || 'Trusted by Families Across Singapore'}
          </h2>
          <p className="text-charcoal/60 max-w-2xl mx-auto">
            {t('description') || 'Real stories from real customers who have experienced the Aqina difference.'}
          </p>
        </div>

        {/* Testimonials Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <div
              key={index}
              className="relative p-8 bg-white rounded-3xl shadow-lg border border-charcoal/5 hover:shadow-xl transition-all"
            >
              {/* Quote Icon */}
              <div className="absolute top-6 right-6 text-primary/20">
                <Quote size={48} />
              </div>

              {/* Content */}
              <div className="space-y-6">
                {/* Stars */}
                <div className="flex gap-1">
                  {Array.from({ length: testimonial.stars }).map((_, i) => (
                    <Star key={i} size={18} className="fill-yellow-400 text-yellow-400" />
                  ))}
                </div>

                {/* Testimonial Text */}
                <p className="text-charcoal/80 leading-relaxed italic">
                  {testimonial.text}
                </p>

                {/* Customer Role */}
                <div className="pt-4 border-t border-charcoal/10">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white font-bold">
                      {testimonial.role.charAt(0)}
                    </div>
                    <span className="font-semibold text-charcoal">{testimonial.role}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
