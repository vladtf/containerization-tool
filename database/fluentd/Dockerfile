FROM fluent/fluentd:edge-debian AS base

USER root

RUN buildDeps="sudo make gcc g++ libc-dev" \
    && apt-get update \
    && apt-get install -y --no-install-recommends $buildDeps \
    && sudo apt-get install -y default-libmysqlclient-dev \
    && sudo gem install fluent-plugin-mysql \
    && sudo gem sources --clear-all \
    && SUDO_FORCE_REMOVE=yes \
    apt-get purge -y --auto-remove \
    -o APT::AutoRemove::RecommendsImportant=false \
    $buildDeps \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/* /usr/lib/ruby/gems/*/cache/*.gem

USER fluent
