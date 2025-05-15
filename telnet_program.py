#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  telnet_program.py
#  
#  Copyright 2025 Emirhan Durak
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
import socket # Network iletisimi icin onemli 
import threading # Buradaki Olay Coklu Istemciyi Desteklemesi Gelen her bir baglanti icin ayri bir is parcacigi olusturuyor kullanilan fonksiyonlarda bunu belirticem.
import subprocess #Dosya islemleri icin hizlica arastirip buldugum bir kutuphane , yazdigimiz girdilerin calisabilmesi icin. 
Network_Host = '192.168.1.77'
port = 23 # On tanimli Port kullandim.


karsilama_ekrani = """
*** The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law. ***

***Telnet-L servisine hoş geldin***     
"""


cikis_ekrani = """

***Telnet-L servisine girdigin icin tesekkur ederim***     



"""



#Direk chatgptden ornek alip ekledim otomatik olarak sunucuya girdikten sonra help menusu acildigi zaman izin verilen girdiler
yardim_secenekler = {
    "***Girdi Secenekleri": "***",
    "\nls": "Dizindeki dosyalari listeler",
    "\ndf": "Disk kullanimi bilgisi verir",
    "\nfree": "Bellek bilgisi verir",
    "\nwhoami": "Mevcut kullanici adini verir",
    "\nclear": "Ekrani temizler (istemci tarafinda degil)",
    "\necho": "Verilen metni tekrar yazar",
    "\n? / help": "Kullanilabilir komutlari listeler"
}




#Her bir istemci baglantisi icin calisan ayri ayri is parcacigi icin fonksiyon bagl = baglanti , adre = adres
def istemci_baglantisi(bagl,adre): 
	
 try:
     print(f"[/]Baglanti Geldi: {adre}")  # Baglantinin Gelmesi Ardindan Yapan Kisinin Ipv4 Adresinin Yazilmasi
     bagl.sendall(karsilama_ekrani.encode('utf-8'))  ## senall() fonksiyonu gonderme islevide fakat biz burada sunucu oldugumuz icin baglanti oldugu zaman bizim tarafimizda yanit gelmesi lazim oyuzden yanit icin bu fonksiyon yazildi bide hos geldin ekraninda ise en basta b olmasinin sebebi bayt'dan metne cevirmesi cunku telnet metin tabanli bir network protokolu
     kullanici_dogrulama(bagl)

     while True:
         try:
             bagl.sendall(b"> ")
             veri = bagl.recv(4096)
             if not veri:
                 break

             komut = veri.decode('utf-8', errors='ignore').strip()  # Yazilmasinin sebebi ise stringin duzgun gelmesi yani bir stringin basindaki ve sonundaki bosluklari , tab karakterlini veyahut satir sonlarini siliyor yani adam komut yazarken misal exit yazarken exit/n gibi birsey olmuyor adam direk exit girdisini giriyor ve benim yazdigim seyde exit/n gibi bir ifadede yani asagidaki if yapisinda sadece exit olarak anlasilmasi icin iste anlamissinizdir.Bide errors ignore eklenerek gecersiz karakterleri atliyor komutlar duzgun calisiyor

             if komut.lower() in ['exit', 'quit', 'Ctrl-c']:  # eger adamin yazdigi komut,exit ve quit listesinden herhangi biri ise direk cikiyo 
                 bagl.sendall(cikis_ekrani.encode('utf-8'))
                 bagl.close()
                 break
             else:
                 yanit = dosya_islemleri(komut, bagl) + telnet_secenek(bagl, komut)  ## baska komutun ciktilarini buraya aktardik cunku ayri ayri is parcacigi islevindeyken sunucuya giren istemcilerin yazdigi exit ve quit haricindeki komutlar burdaki else kismina dosya_islemleri fonksiyonunu ekledim. 
                 bagl.sendall(yanit.encode('utf-8'))  # Adam direk komutu yazdi , yazdigi komut bana geldi encode olarak.
         except Exception as komut_hata:
             print("Komut Hatasi: ", komut_hata)

 except Exception as baglanti_hata:
     print("Baglanti Hatasi: ", baglanti_hata)

			 	


def kullanici_dogrulama(bagl):
	try:
		with open("kullanici_bilgileri.txt", "r", encoding="utf-8") as dosya:
		    icerik = dosya.read().strip()
		
		bagl.sendall(b"Kullanici Adi: ")
		giris = bagl.recv(1024).decode('utf-8', errors='ignore').strip()
		
		with open("sifreler.txt", "r", encoding="utf-8") as dosya1:
		    icerik1 = dosya1.read().strip()
		
		bagl.sendall(b"Sifre: ")
		giris1 = bagl.recv(1024).decode('utf-8', errors='ignore').strip()
		
		if giris in icerik and giris1 in icerik1:
		    bagl.sendall((giris + "" + giris1).encode('utf-8'))
		    return True # Dogru Ciktiyi Dondursun
		else:
			bagl.sendall(b"[/] Hatali Giris Tekrar Deneyiniz.\n")
			return False # Yanlis ciktiyi dondursun
	except Exception as kullanici_dogrulama_hatasi:
		print(f"Dogrulama Hatasi {kullanici_dogrulama_hatasi} ")
		return False # Buradaki islevin tamamen hatali olmasi durumunda False deger dondurmesi
		
# Istemcimiz(lerimiz) sunucuya baglandiktan sonra ayri is parcaciklari gibi islevler yerine getirildiginde artik dosya islemlerini dahil ediyoruz bunun icin subprocess adinda bir kutuphane buldum direk chatgpt ye sordum kisacasi hemen bilgi almak icin
def dosya_islemleri(komut, bagl): # Dosya islemleriyle alakali fonksiyonu olusturduk ve mantiken yazacagimiz komutlari "komut" ismini parametre olarak verdim    
    komut = komut.strip().split()[0] # Dizeden eleman aliyor ve asagidaki izinli_komutlar listesindekiler haric girdi girildiginde girdi onaylanmiyor
    izinli_komutlar = ['ls','df','clear','free','whoami','echo','Echo','?','help']

    if komut.lower() not in izinli_komutlar:
        bagl.sendall("\n".encode('utf-8')) # Yanit islevi 
        return ""
    else:
        try:
            sonuc = subprocess.run(komut, shell=True, capture_output=True, text=True) # subprocess yani bu islevi calistirip yazdigim komutlari terminalde alip calistirip standart ciktilari ve hatali ciktlilarida alip ardindan byte degilde metin olarak aktarabilmesine yarayan fonksiyonu ve parametrelerini dahil ettim.
            stderr=subprocess.PIPE #Stderr ciktilarinin olmamasi yani yazdigim komutlarin hata ciktisinin ortadan kalkmasi bunuda subprocess.PIPE parametresi ile kontrol ediyoruz
            return sonuc.stdout + sonuc.stderr # subprocessin dondurdugu cikti bide hata ciktisini birlestirip donduruyor yani hem hatasiz hem hatali komutlar icin lazim burasi daha anlatmak gerekirse stdout kismi misal ben ls yazdigim zaman bu komutun ciktisini veriyor. stderr kismi ise bir linux girdisini (komutu) yanlis yazdigim zaman bana ciktisini veriyor
            
        except Exception as dosya_islemleri_hata:
            return f"Hata {dosya_islemleri_hata}"			

def telnet_secenek(bagl, komut):                
    try:
        if komut.lower() in ['?','help']:
            yanit = "\n".join([f"{key}: {value}" for key, value in yardim_secenekler.items()]) # anahtar ve degeler icin hepsini .items() ile yaptik buda bir sozluk icindeki tum anahtar cift verilerini dondurmeye yariyor ve bu sozluk icindeki tum verileri donguyle gezebiliriz.
            return yanit + "\n"
        else:
            print("\n")
            return ""
    except Exception as telnet_secenek_hata:
        return f"Hata {telnet_secenek_hata}" # Hatayi F string halde donduruyor		
		
			

def sunucu_baslamasi(): # Ana Sunucu Yeri (Ana fonksiyonlar) 
	
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP ve ipv4 olacak sekilde bir soket.

	server.bind((Network_Host, port))

	server.listen(5) #Maksimum 5 tane makineyi kuyruga alacak.
	print(f"[/]Telnet Sunucusu icin {Network_Host}:{port} Network Adresinde Dinleniyor")


	while True:
		bagl, adre = server.accept() #Baglantiyi Kabul Etsin
		client_thread = threading.Thread(target=istemci_baglantisi, args=(bagl,adre)) ## Burdaki olayda anladigim kadariyla ayri is parcaciklarinin olmasi icin target kisminda fonksiyonu calistirip ardindan fonksiyon icindeki argumanlari args ile tanimlayip ayri is parcacigi mevzusunu gecerli hale getiriyoruz.	
		client_thread.start() # Tahminimce burda Baslatiyoruz


# Programin Baslamasi
if __name__ == "__main__":
	sunucu_baslamasi()
