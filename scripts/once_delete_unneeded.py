from catalogue.models import Book


slugs = """sienkiewicz__ogniem_i_mieczem__tom_1
sienkiewicz__ogniem_i_mieczem__tom_2
czechowicz__dzien_jak_codzien
czechowicz__erotyk_elegia_niemocy_elegia_zalu_elegia_uspienia
czechowicz__imieniny_pod_piopiolem_sam_pontorson
czechowicz__preludjum_ballada_o_matce_przez_kresy
czechowicz__zdrada_samobojstwo_deszcz_w_przeczucia
brzozowski__legaenda_mlodej_polski__cz_1
brzozowski__legaenda_mlodej_polski__cz_2
brzozowski__legaenda_mlodej_polski__cz_3
brzozowski__legaenda_mlodej_polski__cz_4
brzozowski__legaenda_mlodej_polski__cz_5
brzozowski__legaenda_mlodej_polski__cz_6
brzozowski__legaenda_mlodej_polski__cz_7
ayenarius__noc_byla
mickiewicz__zdania_i_uwagi
mickiewicz__pan_tadeusz__ksiegi_1-6
mickiewicz__pan_tadeusz__ksiegi_7-12
sienkiewicz__potop__tom_1__rozdzialy_7-26
sienkiewicz__potop__tom_2
sienkiewicz__pan_wolodyjowski__rozdzialy_53-54_i_epilog"""

Book.objects.filter(slug__in=slugs.split()).delete()


