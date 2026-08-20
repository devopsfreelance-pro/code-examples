# Rocky Linux 9 es un clon binario-compatible de RHEL, mantiene los mismos
# comandos (rpm, dnf, createrepo_c) sin necesitar una suscripción de Red Hat.
# Sirve para practicar localmente lo que en producción harías contra RHEL.
FROM rockylinux:9

RUN dnf install -y createrepo_c httpd nginx && dnf clean all

WORKDIR /demo
COPY rpm-repo-demo.sh /demo/rpm-repo-demo.sh
RUN chmod +x /demo/rpm-repo-demo.sh

ENTRYPOINT ["/demo/rpm-repo-demo.sh"]
