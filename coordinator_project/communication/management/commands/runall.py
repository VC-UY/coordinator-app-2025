"""
Commande Django pour démarrer le serveur Django ET le proxy Redis simultanément.
Les logs sont séparés dans des fichiers différents.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
import threading
import subprocess
import logging
import os
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Démarre le serveur Django et le proxy Redis avec logs séparés'

    def add_arguments(self, parser):
        parser.add_argument(
            '--django-port',
            type=int,
            default=8100,
            help='Port pour le serveur Django (défaut: 8100)'
        )
        parser.add_argument(
            '--redis-host',
            default='0.0.0.0',
            help='Hôte Redis (défaut: 0.0.0.0)'
        )
        parser.add_argument(
            '--redis-port',
            type=int,
            default=6379,
            help='Port Redis (défaut: 6379)'
        )
        parser.add_argument(
            '--proxy-port',
            type=int,
            default=6380,
            help='Port du proxy Redis (défaut: 6380)'
        )
        parser.add_argument(
            '--logs-dir',
            default='logs',
            help='Répertoire pour les logs (défaut: logs/)'
        )

    def handle(self, *args, **options):
        django_port = options['django_port']
        redis_host = options['redis_host']
        redis_port = options['redis_port']
        proxy_port = options['proxy_port']
        logs_dir = options['logs_dir']
        
        # Créer le répertoire de logs s'il n'existe pas
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Chemins des fichiers de logs avec timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        django_log = os.path.join(logs_dir, f'django_{timestamp}.log')
        proxy_log = os.path.join(logs_dir, f'proxy_{timestamp}.log')
        
        # Créer aussi des liens symboliques vers les derniers logs
        django_latest = os.path.join(logs_dir, 'django_latest.log')
        proxy_latest = os.path.join(logs_dir, 'proxy_latest.log')
        
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('🚀 DÉMARRAGE DES SERVICES COORDINATOR'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'📊 Serveur Django:'))
        self.stdout.write(f'   • Port: {django_port}')
        self.stdout.write(f'   • URL: http://0.0.0.0:{django_port}')
        self.stdout.write(f'   • Logs: {django_log}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'🔄 Proxy Redis:'))
        self.stdout.write(f'   • Redis: {redis_host}:{redis_port}')
        self.stdout.write(f'   • Proxy: {proxy_port}')
        self.stdout.write(f'   • Logs: {proxy_log}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'📁 Proxy de fichiers:'))
        self.stdout.write(f'   • Port: 8410')
        self.stdout.write(f'   • URL: http://0.0.0.0:8410/files/')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write('')
        
        # Démarrer le proxy Redis dans un sous-processus
        self.stdout.write(self.style.WARNING('⚙️  Démarrage du proxy Redis...'))
        
        proxy_cmd = [
            sys.executable,  # Python interpreter
            'manage.py',
            'start_redis_proxy',
            '--redis-host', redis_host,
            '--redis-port', str(redis_port),
            '--proxy-port', str(proxy_port)
        ]
        
        proxy_log_file = open(proxy_log, 'w')
        proxy_process = subprocess.Popen(
            proxy_cmd,
            stdout=proxy_log_file,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True
        )
        
        # Créer le lien symbolique pour proxy_latest.log
        if os.path.exists(proxy_latest):
            os.remove(proxy_latest)
        os.symlink(os.path.abspath(proxy_log), proxy_latest)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Proxy Redis démarré (PID: {proxy_process.pid})'))
        self.stdout.write(f'   📝 Logs: tail -f {proxy_log}')
        self.stdout.write('')
        
        # Attendre un peu pour s'assurer que le proxy démarre
        import time
        self.stdout.write('⏳ Attente de 10 secondes pour le démarrage du proxy...')
        time.sleep(10)
        
        # Vérifier si le proxy est toujours en cours d'exécution
        if proxy_process.poll() is not None:
            self.stdout.write(self.style.ERROR('❌ Le proxy Redis a échoué au démarrage'))
            self.stdout.write(f'   📝 Vérifiez les logs: {proxy_log}')
            proxy_log_file.close()
            return
        
        # Démarrer le serveur Django dans un sous-processus
        self.stdout.write(self.style.WARNING('⚙️  Démarrage du serveur Django...'))
        
        django_cmd = [
            sys.executable,
            'manage.py',
            'runserver',
            f'0.0.0.0:{django_port}',
            '--noreload'
        ]
        
        django_log_file = open(django_log, 'w')
        django_process = subprocess.Popen(
            django_cmd,
            stdout=django_log_file,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True
        )
        
        # Créer le lien symbolique pour django_latest.log
        if os.path.exists(django_latest):
            os.remove(django_latest)
        os.symlink(os.path.abspath(django_log), django_latest)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Serveur Django démarré (PID: {django_process.pid})'))
        self.stdout.write(f'   📝 Logs: tail -f {django_log}')
        self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('✅ TOUS LES SERVICES SONT DÉMARRÉS'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write('')
        self.stdout.write('💡 Commandes utiles:')
        self.stdout.write(f'   • Logs Django:  tail -f {django_log}')
        self.stdout.write(f'   • Logs Proxy:   tail -f {proxy_log}')
        self.stdout.write(f'   • Logs Django (latest): tail -f {django_latest}')
        self.stdout.write(f'   • Logs Proxy (latest):  tail -f {proxy_latest}')
        self.stdout.write('')
        self.stdout.write('⚠️  Appuyez sur Ctrl+C pour arrêter tous les services')
        self.stdout.write('')
        
        # Garder le processus principal actif et attendre les sous-processus
        try:
            while True:
                # Vérifier si les processus sont toujours en cours
                django_status = django_process.poll()
                proxy_status = proxy_process.poll()
                
                if django_status is not None:
                    self.stdout.write(self.style.ERROR(
                        f'❌ Le serveur Django s\'est arrêté (code: {django_status})'
                    ))
                    proxy_process.terminate()
                    break
                
                if proxy_status is not None:
                    self.stdout.write(self.style.ERROR(
                        f'❌ Le proxy Redis s\'est arrêté (code: {proxy_status})'
                    ))
                    django_process.terminate()
                    break
                
                # Attendre un peu avant la prochaine vérification
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('='*60))
            self.stdout.write(self.style.WARNING('⚠️  ARRÊT DES SERVICES...'))
            self.stdout.write(self.style.WARNING('='*60))
            self.stdout.write('')
            
            # Arrêter les processus
            self.stdout.write('🛑 Arrêt du serveur Django...')
            django_process.terminate()
            try:
                django_process.wait(timeout=5)
                self.stdout.write(self.style.SUCCESS('✅ Serveur Django arrêté'))
            except subprocess.TimeoutExpired:
                self.stdout.write(self.style.WARNING('⏱️  Timeout - Forçage de l\'arrêt...'))
                django_process.kill()
            
            self.stdout.write('🛑 Arrêt du proxy Redis...')
            proxy_process.terminate()
            try:
                proxy_process.wait(timeout=5)
                self.stdout.write(self.style.SUCCESS('✅ Proxy Redis arrêté'))
            except subprocess.TimeoutExpired:
                self.stdout.write(self.style.WARNING('⏱️  Timeout - Forçage de l\'arrêt...'))
                proxy_process.kill()
            
            # Fermer les fichiers de logs
            django_log_file.close()
            proxy_log_file.close()
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('='*60))
            self.stdout.write(self.style.SUCCESS('✅ TOUS LES SERVICES ONT ÉTÉ ARRÊTÉS'))
            self.stdout.write(self.style.SUCCESS('='*60))
            self.stdout.write('')
